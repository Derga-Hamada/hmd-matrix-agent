"""
FastAPI Application Entrypoint for HMD Matrix Agentic Engine.
Exposes endpoints for enqueuing tasks, checking task state in Redis, 
and querying permanent task history from SQLite.
"""
import logging
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

from src.services.queue import TaskQueue
from src.services.database import get_all_task_history, get_task_history_by_id

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("hmd_matrix")

app = FastAPI(
    title="HMD Matrix Agentic Engine API",
    description="Asynchronous multi-agent content generation engine with Redis queue and SQLite persistence.",
    version="1.0.0",
)

queue = TaskQueue()


@app.on_event("startup")
async def startup_event():
    """Connect to Redis queue service on startup."""
    logger.info("Starting HMD Matrix Agentic Engine in development mode.")
    await queue.connect()


@app.on_event("shutdown")
async def shutdown_event():
    """Close Redis queue connection on shutdown."""
    await queue.close()


class TaskPayload(BaseModel):
    task_id: str = Field(..., description="Unique task identifier")
    prompt: str = Field(..., description="Core content topic or prompt to process")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Optional task metadata")


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "online", "system": "HMD Matrix Agentic Engine"}


@app.post("/api/v1/tasks", status_code=status.HTTP_202_ACCEPTED)
async def enqueue_task(payload: TaskPayload):
    """Enqueues a new agent task into the Redis task queue."""
    logger.info(f"Received API request to enqueue task: {payload.task_id}")
    
    task_data = {
        "task_id": payload.task_id,
        "prompt": payload.prompt,
        "metadata": payload.metadata
    }
    
    await queue.push_task("agent_tasks", task_data)
    await queue.update_task_status(payload.task_id, "queued")
    
    return {
        "task_id": payload.task_id,
        "status": "queued",
        "message": "Task submitted successfully."
    }


@app.get("/api/v1/tasks/{task_id}")
async def get_queue_task_status(task_id: str):
    """Checks the real-time status and cached result of a task from Redis."""
    task_data = await queue.get_task_status(task_id)
    if not task_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task '{task_id}' not found in active queue cache."
        )
    return task_data


@app.get("/api/v1/history")
async def fetch_history():
    """Retrieves all processed content tasks from permanent database storage."""
    history = await get_all_task_history()
    return {"count": len(history), "tasks": history}


@app.get("/api/v1/history/{task_id}")
async def fetch_task_history(task_id: str):
    """Retrieves a specific processed content task from permanent database storage."""
    record = await get_task_history_by_id(task_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task record '{task_id}' not found in database."
        )
    return record   