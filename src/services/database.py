"""
Database configuration, SQLAlchemy models, and query helpers for HMD Matrix Engine.
"""
import json
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, String, Text, DateTime, select

DATABASE_URL = "sqlite+aiosqlite:///./hmd_matrix.db"

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
Base = declarative_base()


class TaskRecord(Base):
    __tablename__ = "tasks"

    task_id = Column(String, primary_key=True, index=True)
    status = Column(String, default="success")
    research_output = Column(Text)  
    script_output = Column(Text)    
    social_output = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


async def init_db():
    """Creates the SQLite database and tables if they do not exist."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def persist_task_result(task_id: str, research: dict, script: dict, social: dict):
    """Commits the final executed task to the database."""
    async with AsyncSessionLocal() as session:
        record = TaskRecord(
            task_id=task_id,
            research_output=json.dumps(research),
            script_output=json.dumps(script),
            social_output=json.dumps(social)
        )
        session.add(record)
        await session.commit()


async def get_all_task_history():
    """Retrieves all stored task records from the database."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(TaskRecord).order_by(TaskRecord.created_at.desc()))
        records = result.scalars().all()
        
        history = []
        for rec in records:
            history.append({
                "task_id": rec.task_id,
                "status": rec.status,
                "created_at": rec.created_at.isoformat() if rec.created_at else None,
                "research": json.loads(rec.research_output) if rec.research_output else None,
                "script": json.loads(rec.script_output) if rec.script_output else None,
                "social": json.loads(rec.social_output) if rec.social_output else None,
            })
        return history


async def get_task_history_by_id(task_id: str):
    """Retrieves a single task record by task_id."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(TaskRecord).where(TaskRecord.task_id == task_id))
        rec = result.scalar_one_or_none()
        
        if not rec:
            return None
            
        return {
            "task_id": rec.task_id,
            "status": rec.status,
            "created_at": rec.created_at.isoformat() if rec.created_at else None,
            "research": json.loads(rec.research_output) if rec.research_output else None,
            "script": json.loads(rec.script_output) if rec.script_output else None,
            "social": json.loads(rec.social_output) if rec.social_output else None,
        }