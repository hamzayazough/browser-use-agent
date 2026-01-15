"""
Job Logs API endpoints
"""
from fastapi import APIRouter
from typing import List, Dict, Any

from app.utils.job_logger import JobLogger

router = APIRouter(prefix="/logs", tags=["logs"])


@router.get("/recent", response_model=List[Dict[str, Any]])
async def get_recent_jobs(limit: int = 10):
    """
    Get recent job summaries
    
    Args:
        limit: Maximum number of jobs to return (default: 10)
        
    Returns:
        List of job summaries with status and statistics
    """
    job_logger = JobLogger()
    jobs = job_logger.get_recent_jobs(limit=limit)
    return jobs


@router.get("/{job_id}", response_model=Dict[str, Any])
async def get_job_details(job_id: str):
    """
    Get detailed log for a specific job
    
    Args:
        job_id: Job ID
        
    Returns:
        Complete job log with all stages
    """
    job_logger = JobLogger()
    log_file = job_logger._get_log_file(job_id)
    
    if not log_file.exists():
        return {"error": "Job not found"}
    
    return job_logger._read_log(log_file)
