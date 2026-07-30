"""
FastAPI Application Gateway.

Acts as the primary entry point for external HTTP traffic, routing validated 
requests to the internal asynchronous agent network.
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from src.config.settings import settings
from src.core.logger import logger
from src.core.schemas import AgentRequest, AgentResponse
from src.agents.researcher import ResearchAgent


# Initialize the FastAPI application with metadata from our Pydantic settings
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="API Gateway for the distributed AI agent architecture.",
    docs_url="/docs",  # Auto-generated Swagger UI
)

@app.on_event("startup")
async def startup_event():
    """Executes necessary setup when the server boots."""
    logger.info(f"Starting {settings.PROJECT_NAME} in {settings.ENVIRONMENT} mode.")


@app.get("/health")
async def health_check():
    """Simple health check endpoint for load balancers and container orchestration."""
    return {"status": "healthy", "version": settings.VERSION}


@app.post("/api/v1/research", response_model=AgentResponse)
async def trigger_research_agent(request: AgentRequest):
    """
    Triggers the ResearchAgent to analyze a specific topic or prompt.
    """
    logger.info(f"Received API request to route task: {request.task_id}")
    
    try:
        # Initialize the agent
        agent = ResearchAgent()
        
        # Await the asynchronous execution
        response = await agent.execute(request)
        
        # Check if the agent internally failed and return an appropriate HTTP status
        if response.status == "failed":
            return JSONResponse(status_code=500, content=response.model_dump())
            
        return response

    except Exception as e:
        logger.error(f"Critical API failure on task {request.task_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error during agent execution.")