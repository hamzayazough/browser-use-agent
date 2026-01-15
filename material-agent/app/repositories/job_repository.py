"""
Repository layer for Job tracking CRUD operations
"""
from typing import Optional, List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime

from app.models import JobModel, JobStatus


class JobRepository:
    """Data access layer for background job tracking"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db.jobs
        
    async def create_indexes(self):
        """Create database indexes for optimal query performance"""
        await self.collection.create_index("job_id", unique=True)
        await self.collection.create_index("status")
        await self.collection.create_index("job_type")
        await self.collection.create_index("created_at")
    
    async def create(self, job: JobModel) -> JobModel:
        """Insert a new job"""
        job_dict = job.model_dump(by_alias=True, exclude={"id"})
        result = await self.collection.insert_one(job_dict)
        job.id = str(result.inserted_id)
        return job
    
    async def find_by_job_id(self, job_id: str) -> Optional[JobModel]:
        """Find a job by its unique job_id"""
        doc = await self.collection.find_one({"job_id": job_id})
        if doc:
            return JobModel(**doc)
        return None
    
    async def update_status(
        self, 
        job_id: str, 
        status: JobStatus,
        output_data: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
        progress: Optional[int] = None
    ) -> Optional[JobModel]:
        """Update job status and related fields"""
        update_data: Dict[str, Any] = {
            "status": status,
            "updated_at": datetime.utcnow()
        }
        
        if output_data is not None:
            update_data["output_data"] = output_data
        
        if error_message is not None:
            update_data["error_message"] = error_message
        
        if progress is not None:
            update_data["progress"] = progress
        
        if status == JobStatus.COMPLETED or status == JobStatus.FAILED:
            update_data["completed_at"] = datetime.utcnow()
        
        result = await self.collection.find_one_and_update(
            {"job_id": job_id},
            {"$set": update_data},
            return_document=True
        )
        
        if result:
            return JobModel(**result)
        return None
    
    async def list_jobs(
        self,
        status: Optional[JobStatus] = None,
        job_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[JobModel]:
        """List jobs with optional filtering"""
        query: Dict[str, Any] = {}
        
        if status:
            query["status"] = status
        if job_type:
            query["job_type"] = job_type
        
        cursor = self.collection.find(query).sort("created_at", -1).skip(skip).limit(limit)
        jobs = []
        async for doc in cursor:
            jobs.append(JobModel(**doc))
        return jobs
    
    async def delete(self, job_id: str) -> bool:
        """Hard delete a job (for cleanup)"""
        result = await self.collection.delete_one({"job_id": job_id})
        return result.deleted_count > 0
