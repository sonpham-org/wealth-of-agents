from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
import uuid
import json
from datetime import datetime
from pathlib import Path
import asyncio
import subprocess
import shutil
from storage import get_storage_manager

app = FastAPI(title="Wealth of Agents API", version="1.0.0")

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store jobs in memory (in production, use database)
jobs_db: Dict[str, Dict[str, Any]] = {}

# Use existing output directory structure
OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

# Serve static visualizer files
VISUALIZER_PATH = Path("visualizer.html")
if VISUALIZER_PATH.exists():
    # Mount output directory as static files
    app.mount("/output", StaticFiles(directory="output"), name="output")


class SimulationConfig(BaseModel):
    """Configuration for a simulation job"""
    num_agents: int = Field(default=10, ge=2, le=1000, description="Number of agents")
    num_steps: int = Field(default=100, ge=10, le=10000, description="Simulation steps")
    initial_money: float = Field(default=1000.0, ge=0, description="Initial money per agent")
    use_money_issuer: bool = Field(default=False, description="Enable central bank")
    use_cognitive_agents: bool = Field(default=False, description="Enable LLM reasoning")
    commodities: List[str] = Field(default=["Grain", "Iron", "Wood", "Stone"])
    description: Optional[str] = Field(default=None, description="Job description")


class Job(BaseModel):
    """Simulation job"""
    id: str
    status: str  # pending, running, completed, failed
    config: SimulationConfig
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    result_path: Optional[str] = None
    error: Optional[str] = None


def run_simulation_sync(job_id: str, config: SimulationConfig):
    """Run simulation synchronously using existing run_simulation.py"""
    try:
        # Update job status
        jobs_db[job_id]["status"] = "running"
        jobs_db[job_id]["started_at"] = datetime.now().isoformat()
        
        # Generate timestamp-based run_id for output directory
        run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = OUTPUT_DIR / run_id
        
        # Build command using existing run_simulation.py
        cmd = [
            "python", "run_simulation.py",
            "--agents", str(config.num_agents),
            "--ticks", str(config.num_steps),
        ]
        
        if config.use_money_issuer:
            cmd.append("--money-printing")
        
        if config.use_cognitive_agents:
            cmd.append("--use-llm")
        
        # Run simulation
        result = subprocess.run(
            cmd,
            cwd=Path(__file__).parent.parent,
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout
        )
        
        if result.returncode == 0:
            # Simulation creates output/TIMESTAMP/ directory automatically
            # Store reference to it
            jobs_db[job_id]["status"] = "completed"
            jobs_db[job_id]["completed_at"] = datetime.now().isoformat()
            jobs_db[job_id]["run_id"] = run_id
            jobs_db[job_id]["output_path"] = str(output_path)
            
            # Upload to cloud storage
            storage = get_storage_manager()
            storage_result = storage.save_simulation_output(run_id, output_path)
            jobs_db[job_id]["storage"] = storage_result
            
            # Update list_runs.json
            update_runs_list()
        else:
            jobs_db[job_id]["status"] = "failed"
            jobs_db[job_id]["error"] = result.stderr
            jobs_db[job_id]["completed_at"] = datetime.now().isoformat()
            
    except Exception as e:
        jobs_db[job_id]["status"] = "failed"
        jobs_db[job_id]["error"] = str(e)
        jobs_db[job_id]["completed_at"] = datetime.now().isoformat()


def update_runs_list():
    """Update list_runs.json with all completed simulations"""
    try:
        from generate_run_list import generate_run_list
        generate_run_list()
    except Exception as e:
        print(f"Failed to update runs list: {e}")


async def run_simulation_async(job_id: str, config: SimulationConfig):
    """Run simulation in background"""
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, run_simulation_sync, job_id, config)


@app.get("/")
def root():
    """API health check"""
    return {
        "service": "Wealth of Agents API",
        "status": "running",
        "version": "1.0.0"
    }


@app.post("/jobs", response_model=Job)
async def create_job(config: SimulationConfig, background_tasks: BackgroundTasks):
    """Create and start a new simulation job"""
    job_id = str(uuid.uuid4())
    
    job = {
        "id": job_id,
        "status": "pending",
        "config": config.dict(),
        "created_at": datetime.now().isoformat(),
        "started_at": None,
        "completed_at": None,
        "result_path": None,
        "error": None
    }
    
    jobs_db[job_id] = job
    
    # Run simulation in background
    background_tasks.add_task(run_simulation_async, job_id, config)
    
    return Job(**job)


@app.get("/jobs", response_model=List[Job])
def list_jobs():
    """List all simulation jobs"""
    return [Job(**job) for job in jobs_db.values()]


@app.get("/jobs/{job_id}", response_model=Job)
def get_job(job_id: str):
    """Get job details"""
    if job_id not in jobs_db:
        raise HTTPException(status_code=404, detail="Job not found")
    return Job(**jobs_db[job_id])


@app.get("/jobs/{job_id}/results")
def get_job_results(job_id: str):
    """Get job results from output directory"""
    if job_id not in jobs_db:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs_db[job_id]
    
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail=f"Job is {job['status']}, not completed")
    
    # Return path to visualizer
    run_id = job.get("run_id")
    if not run_id:
        raise HTTPException(status_code=404, detail="Run ID not found")
    
    output_path = OUTPUT_DIR / run_id
    if not output_path.exists():
        raise HTTPException(status_code=404, detail="Output directory not found")
    
    # Return metadata and path to visualization
    return {
        "job_id": job_id,
        "run_id": run_id,
        "output_path": str(output_path),
        "visualizer_url": f"/visualizer?run={run_id}",
        "config": job["config"],
        "created_at": job["created_at"],
        "completed_at": job["completed_at"]
    }


@app.get("/runs")
def list_runs():
    """List all simulation runs from list_runs.json"""
    list_runs_path = Path("list_runs.json")
    if not list_runs_path.exists():
        return []
    
    with open(list_runs_path) as f:
        return json.load(f)


@app.delete("/jobs/{job_id}")
def delete_job(job_id: str):
    """Delete a job"""
    if job_id not in jobs_db:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Delete result file if exists
    if jobs_db[job_id]["result_path"]:
        result_path = Path(jobs_db[job_id]["result_path"])
        if result_path.exists():
            result_path.unlink()
    
    del jobs_db[job_id]
    return {"message": "Job deleted successfully"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
