"""
Production-ready backend for Railway deployment
Uses PostgreSQL for job persistence and proper async task handling
"""
from fastapi import FastAPI, BackgroundTasks, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime
from pathlib import Path
import os
import uuid
import asyncio
import subprocess
import json

# Database imports (using SQLAlchemy)
from sqlalchemy import create_engine, Column, String, Integer, Float, Boolean, DateTime, Text, JSON, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from api.storage import get_storage_manager

# ============================================================================
# Database Setup
# ============================================================================

# Use /app/data for persistent storage on Railway (volume mount)
DATA_DIR = os.getenv("DATA_DIR", "/app/data" if os.path.exists("/app/data") else ".")
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DATA_DIR}/jobs.db")

# Railway PostgreSQL fix: postgres:// → postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# SQLite for local dev, PostgreSQL for production
connect_args = {"check_same_thread": False} if "sqlite" in DATABASE_URL else {}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    poolclass=StaticPool if "sqlite" in DATABASE_URL else None
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ============================================================================
# Database Models
# ============================================================================

class JobDB(Base):
    """Job model for database persistence"""
    __tablename__ = "jobs"
    
    id = Column(String, primary_key=True, index=True)
    status = Column(String, index=True)  # pending, running, completed, failed
    
    # Configuration
    num_agents = Column(Integer)
    num_steps = Column(Integer)
    initial_money = Column(Float)
    use_money_issuer = Column(Boolean)
    use_cognitive_agents = Column(Boolean)
    commodities = Column(JSON)
    description = Column(String, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Results
    run_id = Column(String, nullable=True, index=True)
    storage_location = Column(String, nullable=True)
    storage_info = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)


# Create tables
Base.metadata.create_all(bind=engine)


# ============================================================================
# Pydantic Models (API)
# ============================================================================

class SimulationConfig(BaseModel):
    """Configuration for a simulation job"""
    num_agents: int = Field(default=10, ge=2, le=1000)
    num_steps: int = Field(default=100, ge=10, le=10000)
    initial_money: float = Field(default=1000.0, ge=0)
    use_money_issuer: bool = Field(default=False)
    use_cognitive_agents: bool = Field(default=False)
    commodities: List[str] = Field(default=["Grain", "Iron", "Wood", "Stone"])
    description: Optional[str] = None


class Job(BaseModel):
    """Simulation job response"""
    id: str
    status: str
    config: dict
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    run_id: Optional[str] = None
    storage_location: Optional[str] = None
    error: Optional[str] = None
    
    class Config:
        from_attributes = True


# ============================================================================
# FastAPI App
# ============================================================================

app = FastAPI(
    title="Wealth of Agents API",
    version="2.0.0",
    description="Production-ready economic simulation API"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Database Dependency
# ============================================================================

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================================================
# Background Task Functions
# ============================================================================

async def run_simulation_async(job_id: str, config: SimulationConfig):
    """Run simulation in background with proper error handling"""
    db = SessionLocal()
    
    try:
        # Update status to running
        job = db.query(JobDB).filter(JobDB.id == job_id).first()
        if not job:
            return
        
        job.status = "running"
        job.started_at = datetime.utcnow()
        db.commit()
        
        # Generate run_id
        run_id = datetime.now().strftime("%Y%m%d_%H%M%S") + f"_{job_id[:8]}"
        
        # Build simulation command
        cmd = [
            "python", "run_simulation.py",
            "--agents", str(config.num_agents),
            "--ticks", str(config.num_steps),
        ]
        
        if config.use_money_issuer:
            cmd.append("--money-printing")
        
        if config.use_cognitive_agents:
            cmd.append("--enable-llm")
        
        # Run simulation
        process = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=Path(__file__).parent.parent,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=1800  # 30 minute timeout for large simulations
        )
        
        if process.returncode == 0:
            # Success - find the output directory
            output_dir = Path("output") / run_id.split("_")[0] + "_" + run_id.split("_")[1]
            
            # If exact match not found, get latest
            if not output_dir.exists():
                output_base = Path("output")
                if output_base.exists():
                    dirs = sorted([d for d in output_base.iterdir() if d.is_dir()], 
                                 key=lambda x: x.stat().st_mtime, reverse=True)
                    if dirs:
                        output_dir = dirs[0]
            
            # Upload to cloud storage
            storage = get_storage_manager()
            storage_result = storage.save_simulation_output(run_id, output_dir)
            
            # Update job
            job.status = "completed"
            job.completed_at = datetime.utcnow()
            job.run_id = run_id
            job.storage_location = storage_result.get("location")
            job.storage_info = storage_result
            db.commit()
            
        else:
            # Failed
            job.status = "failed"
            job.completed_at = datetime.utcnow()
            job.error_message = stderr.decode() if stderr else "Unknown error"
            db.commit()
    
    except asyncio.TimeoutError:
        job.status = "failed"
        job.completed_at = datetime.utcnow()
        job.error_message = "Simulation timeout (exceeded 30 minutes)"
        db.commit()
    
    except Exception as e:
        job.status = "failed"
        job.completed_at = datetime.utcnow()
        job.error_message = str(e)
        db.commit()
    
    finally:
        db.close()


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/")
def root():
    """API root - redirect to docs"""
    return RedirectResponse(url="/docs")


@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    """Health check endpoint for Railway"""
    try:
        # Check database connection
        db.execute(text("SELECT 1"))
        
        # Check storage
        storage = get_storage_manager()
        
        return {
            "status": "healthy",
            "service": "wealth-of-agents-api",
            "version": "2.0.0",
            "database": "connected",
            "storage_type": storage.storage_type,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Unhealthy: {str(e)}")


@app.post("/jobs", response_model=Job)
async def create_job(
    config: SimulationConfig,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Create and start a new simulation job"""
    
    # Create job in database
    job_id = str(uuid.uuid4())
    
    db_job = JobDB(
        id=job_id,
        status="pending",
        num_agents=config.num_agents,
        num_steps=config.num_steps,
        initial_money=config.initial_money,
        use_money_issuer=config.use_money_issuer,
        use_cognitive_agents=config.use_cognitive_agents,
        commodities=config.commodities,
        description=config.description
    )
    
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    
    # Start background task
    background_tasks.add_task(run_simulation_async, job_id, config)
    
    return Job(
        id=db_job.id,
        status=db_job.status,
        config=config.dict(),
        created_at=db_job.created_at
    )


@app.get("/jobs", response_model=List[Job])
def list_jobs(
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """List all jobs with optional filtering"""
    query = db.query(JobDB)
    
    if status:
        query = query.filter(JobDB.status == status)
    
    jobs = query.order_by(JobDB.created_at.desc()).offset(offset).limit(limit).all()
    
    return [
        Job(
            id=job.id,
            status=job.status,
            config={
                "num_agents": job.num_agents,
                "num_steps": job.num_steps,
                "initial_money": job.initial_money,
                "use_money_issuer": job.use_money_issuer,
                "use_cognitive_agents": job.use_cognitive_agents,
                "commodities": job.commodities,
                "description": job.description
            },
            created_at=job.created_at,
            started_at=job.started_at,
            completed_at=job.completed_at,
            run_id=job.run_id,
            storage_location=job.storage_location,
            error=job.error_message
        )
        for job in jobs
    ]


@app.get("/jobs/{job_id}", response_model=Job)
def get_job(job_id: str, db: Session = Depends(get_db)):
    """Get job details by ID"""
    job = db.query(JobDB).filter(JobDB.id == job_id).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return Job(
        id=job.id,
        status=job.status,
        config={
            "num_agents": job.num_agents,
            "num_steps": job.num_steps,
            "initial_money": job.initial_money,
            "use_money_issuer": job.use_money_issuer,
            "use_cognitive_agents": job.use_cognitive_agents,
            "commodities": job.commodities,
            "description": job.description
        },
        created_at=job.created_at,
        started_at=job.started_at,
        completed_at=job.completed_at,
        run_id=job.run_id,
        storage_location=job.storage_location,
        error=job.error_message
    )


@app.delete("/jobs/{job_id}")
def delete_job(job_id: str, db: Session = Depends(get_db)):
    """Delete a job and its results"""
    job = db.query(JobDB).filter(JobDB.id == job_id).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Delete from storage if exists
    if job.run_id:
        try:
            storage = get_storage_manager()
            storage.delete_run(job.run_id)
        except Exception as e:
            print(f"Failed to delete storage: {e}")
    
    # Delete from database
    db.delete(job)
    db.commit()
    
    return {"message": f"Job {job_id} deleted"}


@app.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    """Get overall statistics"""
    total_jobs = db.query(JobDB).count()
    completed_jobs = db.query(JobDB).filter(JobDB.status == "completed").count()
    failed_jobs = db.query(JobDB).filter(JobDB.status == "failed").count()
    running_jobs = db.query(JobDB).filter(JobDB.status == "running").count()
    pending_jobs = db.query(JobDB).filter(JobDB.status == "pending").count()
    
    return {
        "total_jobs": total_jobs,
        "completed": completed_jobs,
        "failed": failed_jobs,
        "running": running_jobs,
        "pending": pending_jobs,
        "storage_type": get_storage_manager().storage_type
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
