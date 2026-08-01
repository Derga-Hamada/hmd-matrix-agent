"""
FastAPI Application Gateway.

Acts as the primary entry point for external HTTP traffic, routing validated 
requests to the internal asynchronous Redis task queue.
"""

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse

from src.config.settings import settings
from src.core.logger import logger
from src.core.schemas import AgentRequest, AgentResponse
from src.services.queue import TaskQueue

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="API Gateway for the distributed AI agent architecture.",
    docs_url="/docs",
)

# Initialize the task queue connection globally
task_queue = TaskQueue(settings.REDIS_URL)

@app.on_event("startup")
async def startup_event():
    """Executes necessary setup when the server boots."""
    logger.info(f"Starting {settings.PROJECT_NAME} in {settings.ENVIRONMENT} mode.")
    await task_queue.connect()

@app.on_event("shutdown")
async def shutdown_event():
    """Cleans up connections when the server stops."""
    await task_queue.close()

@app.get("/health")
async def health_check():
    """Simple health check endpoint."""
    return {"status": "healthy", "version": settings.VERSION}

@app.post("/api/v1/tasks", status_code=status.HTTP_202_ACCEPTED)
async def submit_task(request: AgentRequest):
    """
    Submits a task to the background queue for asynchronous processing.
    """
    logger.info(f"Received API request to enqueue task: {request.task_id}")
    
    try:
        # Push the task to the Redis queue instead of processing it directly
        await task_queue.enqueue_task(queue_name="agent_tasks", request=request)
        
        # Return a 202 Accepted response indicating the task is queued
        return {"task_id": request.task_id, "status": "queued", "message": "Task submitted successfully."}

    except Exception as e:
        logger.error(f"Failed to enqueue task {request.task_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error during task queuing.")

@app.get("/api/v1/tasks/{task_id}", response_model=AgentResponse)
async def get_task_result(task_id: str):
    """
    Retrieves the execution result of a specific task from the Redis cache.
    """
    try:
        result = await task_queue.get_result(task_id)
        
        if not result:
            # If the result isn't in Redis yet, it might still be processing or it doesn't exist
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND, 
                content={"task_id": task_id, "status": "processing_or_not_found"}
            )
            
        return result

    except Exception as e:
        logger.error(f"Error retrieving result for task {task_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error while fetching results.")