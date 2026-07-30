"""
Asynchronous Task Queue Broker Service.

Interfaces with Redis to manage background job distribution and execution state caching.
"""

from typing import Optional
import redis.asyncio as redis

from src.config.settings import settings
from src.core.logger import logger
from src.core.schemas import AgentRequest, AgentResponse


class TaskQueue:
    """Redis-backed asynchronous broker and state store."""

    def __init__(self, redis_url: str = settings.REDIS_URL):
        self.redis_url = redis_url
        self.redis_client: Optional[redis.Redis] = None

    async def connect(self):
        """Establishes connection pool to Redis server."""
        if not self.redis_client:
            self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
            logger.info("Connected to Redis Task Queue service.")

    async def enqueue_task(self, queue_name: str, request: AgentRequest) -> bool:
        """Pushes an agent request payload into the specified queue."""
        if not self.redis_client:
            await self.connect()
            
        payload = request.model_dump_json()
        await self.redis_client.rpush(queue_name, payload)
        logger.info(f"Task {request.task_id} successfully pushed to queue '{queue_name}'.")
        return True

    async def store_result(self, task_id: str, response: AgentResponse, ttl: int = 3600):
        """Caches execution output in Redis with an expiration time (TTL)."""
        if not self.redis_client:
            await self.connect()
            
        key = f"result:{task_id}"
        await self.redis_client.set(key, response.model_dump_json(), ex=ttl)
        logger.info(f"Execution output cached for task: {task_id}")

    async def get_result(self, task_id: str) -> Optional[AgentResponse]:
        """Retrieves cached execution result by task ID."""
        if not self.redis_client:
            await self.connect()
            
        key = f"result:{task_id}"
        data = await self.redis_client.get(key)
        if data:
            return AgentResponse.model_validate_json(data)
        return None

    async def close(self):
        """Closes Redis connection pool cleanly."""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Redis connection closed.")