"""
Background worker process for executing queued agent tasks with transient error retries,
exponential backoff, database persistence, and webhook notifications.
"""

import asyncio
import json
import logging
import random
from src.agents.researcher import ResearchAgent
from src.agents.writer import WriterAgent
from src.agents.social import SocialAgent
from src.services.queue import TaskQueue
from src.services.database import init_db, persist_task_result
from src.services.webhook import send_webhook_notification

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("hmd_matrix")


async def run_agent_with_retry(agent, prompt: str, max_retries: int = 5):
    """Executes an agent with exponential backoff and jitter on transient errors."""
    for attempt in range(1, max_retries + 1):
        result = await agent.process(prompt)
        
        err_msg = str(result.get("error", "")) if isinstance(result, dict) else ""
        
        if any(code in err_msg for code in ["429", "503", "UNAVAILABLE", "RESOURCE_EXHAUSTED", "high demand"]):
            base_backoff = 2 ** attempt
            jitter = random.uniform(0.5, 1.5)
            wait_time = base_backoff * jitter
            
            logger.warning(
                f"Transient API issue on {agent.name}. Retrying in {wait_time:.2f}s "
                f"(Attempt {attempt}/{max_retries})..."
            )
            await asyncio.sleep(wait_time)
        else:
            return result
            
    return result


async def main():
    await init_db()
    
    queue = TaskQueue()
    await queue.connect()

    # Updated model string to gemini-3.6-flash
    research_agent = ResearchAgent(model_name="gemini-3.6-flash")
    writer_agent = WriterAgent(model_name="gemini-3.6-flash")
    social_agent = SocialAgent(model_name="gemini-3.6-flash")

    logger.info("Worker process initialized. Listening on queue: 'agent_tasks'...")

    try:
        while True:
            task = await queue.pop_task("agent_tasks")
            if task:
                if isinstance(task, str):
                    try:
                        task = json.loads(task)
                    except json.JSONDecodeError:
                        logger.error(f"Malformed task string in queue: {task}")
                        continue

                if isinstance(task, dict) and "request" in task and isinstance(task["request"], dict):
                    task = task["request"]

                task_id = task.get("task_id")
                prompt = task.get("prompt")
                metadata = task.get("metadata", {})
                webhook_url = metadata.get("webhook_url") if isinstance(metadata, dict) else None

                if not task_id or not prompt:
                    logger.warning(f"Skipping malformed or empty task payload: {task}")
                    continue

                logger.info(f"Processing task: {task_id}")
                await queue.update_task_status(task_id, "processing")

                # Step 1: Research
                research_res = await run_agent_with_retry(research_agent, prompt)
                await asyncio.sleep(2)

                # Step 2: Writer
                writer_res = await run_agent_with_retry(writer_agent, str(research_res))
                await asyncio.sleep(2)

                # Step 3: Social Media
                social_res = await run_agent_with_retry(social_agent, str(writer_res))

                final_result = {
                    "research": research_res,
                    "script": writer_res,
                    "social": social_res
                }

                # Save temporary state to Redis Queue
                await queue.save_task_result(task_id, final_result)
                
                # Persist to SQLite Database
                await persist_task_result(task_id, research_res, writer_res, social_res)
                
                # Fire Webhook Notification if provided
                if webhook_url:
                    await send_webhook_notification(webhook_url, task_id, "success", final_result)

                logger.info(f"Task {task_id} completed, saved, and notified successfully.")
            else:
                await asyncio.sleep(1)
    except Exception as e:
        logger.error(f"Worker encountered an error: {str(e)}")
    finally:
        await queue.close()


if __name__ == "__main__":
    asyncio.run(main())