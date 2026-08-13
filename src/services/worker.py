"""
Background worker process for the HMD Matrix Engine.
Executes multi-agent orchestration.
"""

import asyncio
import json
import logging
from src.services.queue import TaskQueue    # <-- Changed to import the class
from src.agents.researcher import ResearchAgent
from src.agents.writer import WriterAgent

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] [%(name)s:%(filename)s:%(lineno)d]: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger("hmd_matrix")

# Initialize our queue and agents here
task_queue = TaskQueue()                    # <-- Instantiating the queue object
researcher = ResearchAgent()
writer = WriterAgent()

# ... keep your process_tasks() function below exactly as it is ...