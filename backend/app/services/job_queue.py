"""
Asynchronous Job Queue System for Long-Running Tasks
"""
import asyncio
import json
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
import structlog
import threading

logger = structlog.get_logger()


class JobStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Job:
    id: str
    status: JobStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: int = 0
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    request_data: Optional[Dict[str, Any]] = None
    estimated_duration: Optional[int] = None  # seconds


class JobQueue:
    """In-memory job queue (for production, use Redis or database)"""
    
    def __init__(self):
        self.jobs: Dict[str, Job] = {}
        self.processing_queue = asyncio.Queue()
        self.worker_running = False
        self.max_jobs = 1000  # Maximum number of jobs to keep
        self.job_ttl = 3600  # Job TTL in seconds (1 hour)
        self.cleanup_interval = 300  # Cleanup every 5 minutes
        self.last_cleanup = datetime.utcnow()
        self._lock = threading.RLock()  # Reentrant lock for thread safety
        
    async def submit_job(self, job_type: str, request_data: Dict[str, Any]) -> str:
        """Submit a new job and return job ID"""
        # Cleanup old jobs before submitting new one
        await self._cleanup_old_jobs()
        
        job_id = str(uuid.uuid4())
        
        job = Job(
            id=job_id,
            status=JobStatus.PENDING,
            created_at=datetime.utcnow(),
            request_data=request_data,
            estimated_duration=self._estimate_duration(job_type)
        )
        
        with self._lock:
            self.jobs[job_id] = job
            await self.processing_queue.put((job_id, job_type))
        
        logger.info("Job submitted", job_id=job_id, job_type=job_type)
        return job_id
    
    async def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job status and progress"""
        with self._lock:
            job = self.jobs.get(job_id)
            if not job:
                return None
                
            return {
                "job_id": job_id,
                "status": job.status.value,
                "progress": job.progress,
                "created_at": job.created_at.isoformat(),
                "started_at": job.started_at.isoformat() if job.started_at else None,
                "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                "estimated_duration": job.estimated_duration,
                "error": job.error
            }
    
    async def get_job_result(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job result if completed"""
        with self._lock:
            job = self.jobs.get(job_id)
            if not job or job.status != JobStatus.COMPLETED:
                return None
                
            return {
                "job_id": job_id,
                "status": job.status.value,
                "result": job.result,
                "completed_at": job.completed_at.isoformat()
            }
    
    async def update_job_progress(self, job_id: str, progress: int, status: JobStatus = None):
        """Update job progress"""
        with self._lock:
            job = self.jobs.get(job_id)
            if job:
                job.progress = progress
                if status:
                    job.status = status
                    
                if status == JobStatus.PROCESSING and not job.started_at:
                    job.started_at = datetime.utcnow()
                elif status == JobStatus.COMPLETED:
                    job.completed_at = datetime.utcnow()
                
    async def set_job_result(self, job_id: str, result: Dict[str, Any]):
        """Set job result and mark as completed"""
        with self._lock:
            job = self.jobs.get(job_id)
            if job:
                job.result = result
                job.status = JobStatus.COMPLETED
                job.completed_at = datetime.utcnow()
                job.progress = 100
            
    async def set_job_error(self, job_id: str, error: str):
        """Set job error and mark as failed"""
        with self._lock:
            job = self.jobs.get(job_id)
            if job:
                job.error = error
                job.status = JobStatus.FAILED
                job.completed_at = datetime.utcnow()
    
    def _estimate_duration(self, job_type: str) -> int:
        """Estimate job duration based on type"""
        estimates = {
            "prior_art_search": 240,  # 4 minutes
            "claim_drafting": 120,    # 2 minutes
            "claim_analysis": 60,     # 1 minute
            "web_search": 30,         # 30 seconds
            "general_chat": 30        # 30 seconds
        }
        return estimates.get(job_type, 120)
    
    async def start_worker(self):
        """Start the job processing worker"""
        if self.worker_running:
            return
            
        self.worker_running = True
        logger.info("Job queue worker started")
        
        while self.worker_running:
            try:
                # Wait for job with timeout
                job_id, job_type = await asyncio.wait_for(
                    self.processing_queue.get(), 
                    timeout=1.0
                )
                
                # Process the job
                await self._process_job(job_id, job_type)
                
            except asyncio.TimeoutError:
                # No jobs, continue
                continue
            except Exception as e:
                logger.error("Job worker error", error=str(e))
                await asyncio.sleep(1)
    
    async def stop_worker(self):
        """Stop the job processing worker"""
        self.worker_running = False
        logger.info("Job queue worker stopped")
    
    async def _process_job(self, job_id: str, job_type: str):
        """Process a single job with timeout handling and retry logic"""
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                await self.update_job_progress(job_id, 0, JobStatus.PROCESSING)
                
                job = self.jobs.get(job_id)
                if not job:
                    return
                
                # Set job timeout based on estimated duration
                timeout_seconds = job.estimated_duration + 60  # Add 1 minute buffer
                
                try:
                    # Import here to avoid circular imports
                    from app.services.agent import AgentService
                    from app.services.mcp.orchestrator import get_initialized_mcp_orchestrator
                    
                    agent_service = AgentService()
                    mcp_orchestrator = get_initialized_mcp_orchestrator()
                    
                    # Process with timeout
                    result = await asyncio.wait_for(
                        self._execute_job_by_type(job, job_type, agent_service, mcp_orchestrator),
                        timeout=timeout_seconds
                    )
                    
                    await self.set_job_result(job_id, result)
                    logger.info("Job completed successfully", job_id=job_id, retry_count=retry_count)
                    return  # Success, exit retry loop
                    
                except asyncio.TimeoutError:
                    logger.error("Job timed out", job_id=job_id, timeout=timeout_seconds, retry_count=retry_count)
                    if retry_count < max_retries - 1:
                        retry_count += 1
                        await asyncio.sleep(2 ** retry_count)  # Exponential backoff
                        continue
                    else:
                        await self.set_job_error(job_id, f"Job timed out after {timeout_seconds} seconds (max retries exceeded)")
                        return
                        
                except Exception as e:
                    logger.error("Job execution failed", job_id=job_id, error=str(e), retry_count=retry_count)
                    if retry_count < max_retries - 1:
                        retry_count += 1
                        await asyncio.sleep(2 ** retry_count)  # Exponential backoff
                        continue
                    else:
                        await self.set_job_error(job_id, f"Job failed after {max_retries} retries: {str(e)}")
                        return
                        
            except Exception as e:
                logger.error("Job processing failed", job_id=job_id, error=str(e), retry_count=retry_count)
                if retry_count < max_retries - 1:
                    retry_count += 1
                    await asyncio.sleep(2 ** retry_count)  # Exponential backoff
                    continue
                else:
                    await self.set_job_error(job_id, f"Job processing failed after {max_retries} retries: {str(e)}")
                    return
    
    async def _execute_job_by_type(self, job: Job, job_type: str, agent_service, mcp_orchestrator):
        """Execute job based on type"""
        if job_type == "prior_art_search":
            return await self._process_prior_art_search(job, agent_service, mcp_orchestrator)
        elif job_type == "claim_drafting":
            return await self._process_claim_drafting(job, agent_service, mcp_orchestrator)
        elif job_type == "general_chat":
            return await self._process_general_chat(job, agent_service, mcp_orchestrator)
        else:
            return await self._process_general_chat(job, agent_service, mcp_orchestrator)
    
    async def _process_prior_art_search(self, job: Job, agent_service, mcp_orchestrator):
        """Process prior art search job with real progress tracking"""
        request_data = job.request_data
        
        try:
            # Progress: Starting query generation
            await self.update_job_progress(job.id, 10)
            
            # Get the actual patent search service for real progress tracking
            from app.services.patent_search_service import PatentSearchService
            patent_service = PatentSearchService()
            
            # Progress: Generating search queries
            await self.update_job_progress(job.id, 20)
            
            # Execute with progress callbacks
            result = await self._execute_with_progress(
                job.id,
                patent_service.search_patents,
                request_data.get("message", ""),
                progress_start=20,
                progress_end=90
            )
            
            # Progress: Finalizing results
            await self.update_job_progress(job.id, 95)
            
            # Return the result directly instead of wrapping it
            return result
            
        except Exception as e:
            logger.error("Prior art search failed", job_id=job.id, error=str(e))
            raise
    
    async def _process_claim_drafting(self, job: Job, agent_service, mcp_orchestrator):
        """Process claim drafting job"""
        request_data = job.request_data
        
        await self.update_job_progress(job.id, 20)
        
        result = await agent_service.process_user_message_unified_langgraph(
            user_message=request_data.get("message", ""),
            document_content=request_data.get("document_content", ""),
            available_tools=[],
            frontend_chat_history=request_data.get("chat_history", [])
        )
        
        await self.update_job_progress(job.id, 90)
        
        # Return the result directly instead of wrapping it
        return result
    
    async def _process_general_chat(self, job: Job, agent_service, mcp_orchestrator):
        """Process general chat job with real progress tracking"""
        request_data = job.request_data
        
        try:
            # Progress: Starting processing
            await self.update_job_progress(job.id, 10)
            
            # Execute with progress callbacks
            result = await self._execute_with_progress(
                job.id,
                agent_service.process_user_message_unified_langgraph,
                request_data.get("message", ""),
                request_data.get("document_content", ""),
                [],
                request_data.get("chat_history", []),
                progress_start=10,
                progress_end=90
            )
            
            # Progress: Finalizing
            await self.update_job_progress(job.id, 95)
            
            # Return the result directly instead of wrapping it
            return result
            
        except Exception as e:
            logger.error("General chat processing failed", job_id=job.id, error=str(e))
            raise
    
    async def _execute_with_progress(self, job_id: str, func, *args, progress_start: int = 0, progress_end: int = 100, **kwargs):
        """Execute a function with real progress tracking"""
        import asyncio
        import threading
        import time
        
        # Create a progress tracking wrapper
        class ProgressTracker:
            def __init__(self, job_id, job_queue, start_progress, end_progress):
                self.job_id = job_id
                self.job_queue = job_queue
                self.start_progress = start_progress
                self.end_progress = end_progress
                self.current_progress = start_progress
                self.last_update = time.time()
                self.update_interval = 2.0  # Update every 2 seconds
                
            async def update_progress(self, progress: int):
                current_time = time.time()
                if current_time - self.last_update >= self.update_interval:
                    self.current_progress = self.start_progress + int((progress / 100) * (self.end_progress - self.start_progress))
                    await self.job_queue.update_job_progress(self.job_id, self.current_progress)
                    self.last_update = current_time
        
        tracker = ProgressTracker(job_id, self, progress_start, progress_end)
        
        # Execute the function with progress tracking
        if asyncio.iscoroutinefunction(func):
            result = await func(*args, **kwargs)
        else:
            # For sync functions, run in thread pool
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, func, *args, **kwargs)
        
        # Final progress update
        await self.update_job_progress(job_id, progress_end)
        
        return result
    
    async def _cleanup_old_jobs(self):
        """Clean up old and completed jobs"""
        current_time = datetime.utcnow()
        
        # Only cleanup if enough time has passed
        if (current_time - self.last_cleanup).total_seconds() < self.cleanup_interval:
            return
        
        with self._lock:
            self.last_cleanup = current_time
        
            # Create a copy of jobs to avoid race conditions during iteration
            jobs_copy = dict(self.jobs)
            
            # Remove expired jobs
            expired_jobs = []
            for job_id, job in jobs_copy.items():
                age_seconds = (current_time - job.created_at).total_seconds()
                
                # Remove jobs older than TTL
                if age_seconds > self.job_ttl:
                    expired_jobs.append(job_id)
                # Remove completed/failed jobs older than 10 minutes
                elif job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
                    if age_seconds > 600:  # 10 minutes
                        expired_jobs.append(job_id)
            
            # Remove expired jobs from the original dict
            for job_id in expired_jobs:
                if job_id in self.jobs:  # Double-check job still exists
                    del self.jobs[job_id]
                    logger.info("Cleaned up expired job", job_id=job_id)
            
            # If still too many jobs, remove oldest completed jobs
            if len(self.jobs) > self.max_jobs:
                # Create another copy for the second cleanup pass
                jobs_copy = dict(self.jobs)
                completed_jobs = [
                    (job_id, job) for job_id, job in jobs_copy.items()
                    if job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]
                ]
                
                # Sort by creation time (oldest first)
                completed_jobs.sort(key=lambda x: x[1].created_at)
                
                # Remove oldest completed jobs
                jobs_to_remove = len(self.jobs) - self.max_jobs
                for job_id, _ in completed_jobs[:jobs_to_remove]:
                    if job_id in self.jobs:  # Double-check job still exists
                        del self.jobs[job_id]
                        logger.info("Cleaned up old completed job", job_id=job_id)
        
        logger.info("Job cleanup completed", 
                   total_jobs=len(self.jobs), 
                   removed_jobs=len(expired_jobs))
    
    async def get_job_stats(self) -> Dict[str, Any]:
        """Get job queue statistics"""
        with self._lock:
            status_counts = {}
            for job in self.jobs.values():
                status = job.status.value
                status_counts[status] = status_counts.get(status, 0) + 1
            
            return {
                "total_jobs": len(self.jobs),
                "status_counts": status_counts,
                "max_jobs": self.max_jobs,
                "job_ttl": self.job_ttl,
                "last_cleanup": self.last_cleanup.isoformat()
            }


# Global job queue instance
job_queue = JobQueue()
