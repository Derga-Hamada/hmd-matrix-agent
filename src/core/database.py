"""
Database configuration and models for permanent storage.
"""

from sqlalchemy import create_engine, Column, String, Text, JSON, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
import datetime
import logging

logger = logging.getLogger("hmd_matrix")

# Create a local SQLite database file in the project root
DATABASE_URL = "sqlite:///./hmd_matrix.db"

# Initialize the database engine
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Define the schema for our tasks
class TaskRecord(Base):
    __tablename__ = "tasks"

    id = Column(String, primary_key=True, index=True)
    prompt = Column(Text, nullable=False)
    status = Column(String, default="completed")
    research_data = Column(JSON, nullable=True)
    script_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

# Automatically create the table when this module is imported
logger.info("Initializing SQLite database connection...")
Base.metadata.create_all(bind=engine)