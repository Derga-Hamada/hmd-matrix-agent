"""
Background worker process for the HMD Matrix Engine.
Executes multi-agent orchestration and permanent database storage.
"""

import asyncio
import json
import logging
from src.services.queue import TaskQueue
from src.agents.researcher import ResearchAgent
from src.agents.writer import WriterAgent
from src.core.database import SessionLocal, TaskRecord

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] [%(name)s:%(filename)s:%(lineno)d]: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger("hmd_matrix")

task_queue = TaskQueue()
researcher = ResearchAgent()
writer = WriterAgent()

async def process_tasks():
    logger.info("Worker process initialized. Listening on queue: 'agent_tasks'...")
    
    while True:
        task_data = await task_queue.pop_task("agent_tasks")
        
        if task_data:
            task_id = task_data["task_id"]
            original_prompt = task_data["prompt"]
            logger.info(f"Starting multi-agent pipeline for Task ID: {task_id}")
            
            try:
                # --- PHASE 1: RESEARCH ---
                await task_queue.update_task_status(task_id, "researching")
                research_result = await researcher.process(original_prompt)
                
                if "error" in research_result:
                    raise Exception(research_result["error"])
                
                # --- PHASE 2: SCRIPT WRITING ---
                await task_queue.update_task_status(task_id, "scripting")
                script_result = await writer.process(json.dumps(research_result))
                
                if "error" in script_result:
                    raise Exception(script_result["error"])

                # --- PIPELINE COMPLETE: SAVE TO REDIS ---
                final_output = {
                    "research": research_result,
                    "video_script": script_result
                }
                await task_queue.save_task_result(task_id, final_output)
                
                # --- PHASE 3: PERMANENT STORAGE IN SQLITE ---
                db = SessionLocal()
                try:
                    new_record = TaskRecord(
                        id=task_id,
                        prompt=original_prompt,
                        status="completed",
                        research_data=research_result,
                        script_data=script_result
                    )
                    db.add(new_record)
                    db.commit()
                    logger.info(f"Task ID {task_id} permanently saved to SQLite database.")
                except Exception as db_err:
                    logger.error(f"Database error: {str(db_err)}")
                    db.rollback()
                finally:
                    db.close()
                
                logger.info(f"Pipeline completed successfully for Task ID: {task_id}")
                
            except Exception as e:
                logger.error(f"Pipeline failed for Task ID {task_id}: {str(e)}")
                await task_queue.update_task_status(task_id, "failed")
                await task_queue.save_task_result(task_id, {"error": str(e)})
        else:
            await asyncio.sleep(1)

if __name__ == "__main__":
    try:
        asyncio.run(process_tasks())
    except KeyboardInterrupt:
        logger.info("Worker gracefully shutting down...")