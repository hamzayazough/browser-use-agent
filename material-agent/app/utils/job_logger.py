"""
Job Logger - Save important job information to files
"""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class JobType(str, Enum):
    """Job types"""
    CURRICULUM_DISCOVERY = "curriculum_discovery"
    CONTENT_EXTRACTION = "content_extraction"
    VALIDATION_COVERAGE = "validation_coverage"
    PUBLISH_PACK = "publish_pack"


class JobLogger:
    """Logger for saving job information to files"""
    
    def __init__(self, base_dir: str = "temp"):
        """
        Initialize job logger
        
        Args:
            base_dir: Base directory for logs (relative to project root)
        """
        # Get project root (material-agent directory)
        project_root = Path(__file__).parent.parent.parent
        self.log_dir = project_root / base_dir
        self.log_dir.mkdir(exist_ok=True)
        
        logger.info(f"Job logger initialized: {self.log_dir}")
    
    def start_job(
        self,
        job_type: JobType,
        request_data: Dict[str, Any]
    ) -> str:
        """
        Start a new job and create log file
        
        Args:
            job_type: Type of job
            request_data: Request parameters
            
        Returns:
            Job ID
        """
        timestamp = datetime.utcnow()
        job_id = f"{job_type.value}_{timestamp.strftime('%Y%m%d_%H%M%S')}"
        
        log_file = self.log_dir / f"{job_id}.log"
        
        # Create initial log entry
        log_data = {
            "job_id": job_id,
            "job_type": job_type.value,
            "status": "STARTED",
            "start_time": timestamp.isoformat(),
            "request": request_data,
            "stages": []
        }
        
        self._write_log(log_file, log_data)
        logger.info(f"Started job: {job_id}")
        
        return job_id
    
    def log_stage(
        self,
        job_id: str,
        stage_name: str,
        stage_data: Dict[str, Any],
        status: str = "IN_PROGRESS"
    ):
        """
        Log a job stage
        
        Args:
            job_id: Job ID
            stage_name: Name of the stage
            stage_data: Stage information
            status: Stage status (IN_PROGRESS, COMPLETED, FAILED)
        """
        log_file = self._get_log_file(job_id)
        
        if not log_file.exists():
            logger.warning(f"Log file not found for job: {job_id}")
            return
        
        log_data = self._read_log(log_file)
        
        # Add stage entry
        stage_entry = {
            "stage_name": stage_name,
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
            "data": stage_data
        }
        
        log_data["stages"].append(stage_entry)
        
        self._write_log(log_file, log_data)
        logger.info(f"[{job_id}] Stage logged: {stage_name} - {status}")
    
    def log_discovery_documents(
        self,
        job_id: str,
        documents: List[Dict[str, Any]]
    ):
        """Log discovered official documents"""
        self.log_stage(
            job_id,
            "document_discovery",
            {
                "count": len(documents),
                "documents": [
                    {
                        "title": doc.get("title", "Unknown"),
                        "url": str(doc.get("url", "")),
                        "publisher": doc.get("publisher", "Unknown"),
                        "publication_date": doc.get("publication_date", "Unknown")
                    }
                    for doc in documents
                ]
            },
            status="COMPLETED"
        )
    
    def log_topics_extraction(
        self,
        job_id: str,
        topics: List[Dict[str, Any]]
    ):
        """Log extracted curriculum topics"""
        self.log_stage(
            job_id,
            "topics_extraction",
            {
                "count": len(topics),
                "topics": [
                    {
                        "topic_id": topic.get("topic_id"),
                        "name": topic.get("name"),
                        "objectives_count": len(topic.get("objectives", []))
                    }
                    for topic in topics
                ]
            },
            status="COMPLETED"
        )
    
    def log_oer_search(
        self,
        job_id: str,
        topic_name: str,
        sources_found: int,
        sources: List[Dict[str, Any]]
    ):
        """Log OER source search results"""
        self.log_stage(
            job_id,
            f"oer_search_{topic_name.replace(' ', '_').lower()}",
            {
                "topic": topic_name,
                "sources_found": sources_found,
                "sources": [
                    {
                        "title": src.get("title"),
                        "url": str(src.get("url", "")),
                        "publisher": src.get("publisher"),
                        "content_format": src.get("content_format")
                    }
                    for src in sources
                ]
            },
            status="COMPLETED"
        )
    
    def log_source_vetting(
        self,
        job_id: str,
        total_sources: int,
        vetted_sources: int,
        vetted_list: List[Dict[str, Any]]
    ):
        """Log source vetting results"""
        self.log_stage(
            job_id,
            "source_vetting",
            {
                "total_sources": total_sources,
                "vetted_sources": vetted_sources,
                "vetted_list": [
                    {
                        "title": src.get("title"),
                        "score": src.get("score", 0),
                        "source_type": src.get("source_type")
                    }
                    for src in vetted_list
                ]
            },
            status="COMPLETED"
        )
    
    def log_content_extraction(
        self,
        job_id: str,
        source_id: str,
        source_url: str,
        success: bool,
        chunks_created: int = 0,
        error: Optional[str] = None
    ):
        """Log content extraction from a source"""
        self.log_stage(
            job_id,
            f"extract_{source_id}",
            {
                "source_id": source_id,
                "source_url": source_url,
                "success": success,
                "chunks_created": chunks_created,
                "error": error
            },
            status="COMPLETED" if success else "FAILED"
        )
    
    def log_embeddings(
        self,
        job_id: str,
        chunks_processed: int,
        embeddings_generated: int,
        api_calls: int,
        estimated_cost: float
    ):
        """Log embedding generation"""
        self.log_stage(
            job_id,
            "embedding_generation",
            {
                "chunks_processed": chunks_processed,
                "embeddings_generated": embeddings_generated,
                "api_calls": api_calls,
                "estimated_cost_usd": estimated_cost
            },
            status="COMPLETED"
        )
    
    def complete_job(
        self,
        job_id: str,
        success: bool,
        summary: Dict[str, Any],
        error: Optional[str] = None
    ):
        """
        Mark job as complete
        
        Args:
            job_id: Job ID
            success: Whether job succeeded
            summary: Summary statistics
            error: Error message if failed
        """
        log_file = self._get_log_file(job_id)
        
        if not log_file.exists():
            logger.warning(f"Log file not found for job: {job_id}")
            return
        
        log_data = self._read_log(log_file)
        
        # Calculate duration
        start_time = datetime.fromisoformat(log_data["start_time"])
        end_time = datetime.utcnow()
        duration_seconds = (end_time - start_time).total_seconds()
        
        log_data["status"] = "COMPLETED" if success else "FAILED"
        log_data["end_time"] = end_time.isoformat()
        log_data["duration_seconds"] = duration_seconds
        log_data["summary"] = summary
        
        if error:
            log_data["error"] = error
        
        self._write_log(log_file, log_data)
        logger.info(f"Completed job: {job_id} - {log_data['status']} ({duration_seconds:.2f}s)")
    
    def _get_log_file(self, job_id: str) -> Path:
        """Get log file path for job ID"""
        return self.log_dir / f"{job_id}.log"
    
    def _read_log(self, log_file: Path) -> Dict[str, Any]:
        """Read log file"""
        with open(log_file, 'r') as f:
            return json.load(f)
    
    def _write_log(self, log_file: Path, log_data: Dict[str, Any]):
        """Write log file"""
        with open(log_file, 'w') as f:
            json.dump(log_data, f, indent=2, default=str)
    
    def get_recent_jobs(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent job summaries
        
        Args:
            limit: Maximum number of jobs to return
            
        Returns:
            List of job summaries
        """
        log_files = sorted(
            self.log_dir.glob("*.log"),
            key=lambda f: f.stat().st_mtime,
            reverse=True
        )[:limit]
        
        jobs = []
        for log_file in log_files:
            try:
                log_data = self._read_log(log_file)
                jobs.append({
                    "job_id": log_data["job_id"],
                    "job_type": log_data["job_type"],
                    "status": log_data["status"],
                    "start_time": log_data["start_time"],
                    "duration_seconds": log_data.get("duration_seconds"),
                    "summary": log_data.get("summary", {})
                })
            except Exception as e:
                logger.warning(f"Failed to read log file {log_file}: {e}")
        
        return jobs
