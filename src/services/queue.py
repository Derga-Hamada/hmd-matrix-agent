"""
Redis Task Queue implementation for async job handling.
"""

import json
import logging
from typing import Optional, Any
import redis.asyncio as redis
from src.config.settings import settings

logger = logging.getLogger("hmd_matrix")


class TaskQueue:

    def __init__(self, redis_url: Optional[str] = None):
        url = redis_url or settings.REDIS_URL
        self.redis = redis.from_url(url, decode_responses=True)

    async def connect(self):
        """Verifies the Redis connection during application startup."""
        try:
            await self.redis.ping()
            logger.info("Successfully connected to Redis Task Queue service.")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
            raise e

    async def close(self):
        """Closes the Redis connection pool during application shutdown."""
        try:
            await self.redis.aclose()
            logger.info("Closed Redis connection.")
        except Exception as e:
            logger.error(f"Error closing Redis connection: {str(e)}")

    def _to_dict(self, obj: Any) -> Any:
        """Converts Pydantic models or nested objects to dicts."""
        if hasattr(obj, "model_dump"):
            return obj.model_dump()
        elif hasattr(obj, "dict"):
            return obj.dict()
        elif isinstance(obj, dict):
            return {k: self._to_dict(v) for k, v in obj.items()}
        return obj

    async def push_task(self, queue_name: str, task_data: Any):
        dict_data = self._to_dict(task_data)
        await self.redis.rpush(queue_name, json.dumps(dict_data))

    async def enqueue_task(self, *args, **kwargs):
        queue_name = kwargs.pop("queue_name", "agent_tasks")
        if len(args) == 1:
            task_data = self._to_dict(args[0])
        elif len(args) >= 2:
            task_data = {
                "task_id": args[0],
                "prompt": args[1],
                "metadata": self._to_dict(kwargs.get("metadata", {})) if len(args) < 3 else self._to_dict(args[2])
            }
        elif "task_data" in kwargs:
            task_data = self._to_dict(kwargs["task_data"])
        elif "task_id" in kwargs and "prompt" in kwargs:
            task_data = {
                "task_id": kwargs["task_id"],
                "prompt": kwargs["prompt"],
                "metadata": self._to_dict(kwargs.get("metadata", {}))
            }
        else:
            task_data = self._to_dict(kwargs if kwargs else {"data": args})

        await self.redis.rpush(queue_name, json.dumps(task_data))
        if isinstance(task_data, dict) and "task_id" in task_data:
            await self.update_task_status(task_data["task_id"], "processing")

    async def pop_task(self, queue_name: str = "agent_tasks"):
        result = await self.redis.blpop(queue_name, timeout=2)
        if result:
            return json.loads(result[1])
        return None

    async def update_task_status(self, task_id: str, status: str):
        await self.redis.hset(f"task:{task_id}", "status", status)

    async def get_task_status(self, task_id: str):
        return await self.redis.hget(f"task:{task_id}", "status")

    async def get_task_result(self, task_id: str):
        raw = await self.redis.hget(f"task:{task_id}", "result")
        return json.loads(raw) if raw else None

    async def get_result(self, task_id: str):
        """Fetches status and result formatted for main.py GET route."""
        status = await self.redis.hget(f"task:{task_id}", "status")
        raw_result = await self.redis.hget(f"task:{task_id}", "result")
        
        if not status and not raw_result:
            return None

        parsed_result = None
        if raw_result:
            try:
                parsed_result = json.loads(raw_result)
            except Exception:
                parsed_result = raw_result

        return {
            "task_id": task_id,
            "status": status or "processing",
            "result": parsed_result
        }

    async def get_task(self, task_id: str):
        return await self.get_result(task_id)

    async def save_task_result(self, task_id: str, result: dict):
        # Saved as "success" to satisfy FastAPI Pydantic schema validation regex: ^(success|failed|processing)$
        await self.redis.hset(f"task:{task_id}", "status", "success")
        await self.redis.hset(f"task:{task_id}", "result", json.dumps(result))