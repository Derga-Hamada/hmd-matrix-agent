"""
Background Worker Execution Node.

Continuously polls the Redis task queue, executes assigned AI agents,
and persists execution output.
"""

import asyncio
import json

from src.core.logger import logger
from src.core.schemas import AgentRequest
from src.services.queue import TaskQueue
from src.agents.researcher import ResearchAgent


async def start_worker(queue_name: str = "agent_tasks"):
    """Main event loop for processing background jobs."""
    queue = TaskQueue()
    await queue.connect()
    agent = ResearchAgent()

    logger.info(f"Worker process initialized. Listening on queue: '{queue_name}'...")

    try:
        while True:
            # BLPOP blocks asynchronously until a job arrives on the queue
            result = await queue.redis_client.blpop(queue_name, timeout=2)
            if result:
                _, raw_payload = result
                payload_dict = json.loads(raw_payload)
                request = AgentRequest(**payload_dict)

                logger.info(f"Worker popped task '{request.task_id}'. Initiating execution...")
                
                # Execute agent work
                response = await agent.execute(request)

                # Save response to state store
                await queue.store_result(request.task_id, response)

            await asyncio.sleep(0.1)

    except asyncio.CancelledError:
        logger.info("Worker process shutdown signal received.")
    finally:
        await queue.close()


if __name__ == "__main__":
    try:
        asyncio.run(start_worker())
    except KeyboardInterrupt:
        logger.info("Worker process stopped manually.")