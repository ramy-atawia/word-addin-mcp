"""
Asynchronous Chat API Endpoints
"""
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

from app.services.job_queue import job_queue, JobStatus
import structlog

logger = structlog.get_logger()
router = APIRouter()


class AsyncChatRequest(BaseModel):
    message: str
    context: Dict[str, Any]
    job_type: Optional[str] = "general_chat"


class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    progress: int
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    estimated_duration: Optional[int] = None
    error: Optional[str] = None


class JobResultResponse(BaseModel):
    job_id: str
    status: str
    response: Optional[str] = None
    intent_type: Optional[str] = None
    tool_name: Optional[str] = None
    execution_time: Optional[float] = None
    success: Optional[bool] = None
    error: Optional[str] = None
    workflow_metadata: Optional[Dict[str, Any]] = None
    completed_at: Optional[str] = None


@router.post("/submit", response_model=Dict[str, str])
async def submit_async_chat(request: AsyncChatRequest):
    """
    Submit a chat request for asynchronous processing.
    
    Returns immediately with a job ID that can be used to check status and retrieve results.
    """
    try:
        # Determine job type based on message content
        job_type = _determine_job_type(request.message)
        
        # Prepare request data
        request_data = {
            "message": request.message,
            "document_content": request.context.get("document_content", ""),
            "chat_history": request.context.get("chat_history", []),
            "available_tools": request.context.get("available_tools", "")
        }
        
        # Submit job
        job_id = await job_queue.submit_job(job_type, request_data)
        
        logger.info("Async chat job submitted", 
                   job_id=job_id, 
                   job_type=job_type,
                   message_length=len(request.message))
        
        return {
            "job_id": job_id,
            "status": "accepted",
            "message": "Job submitted successfully. Use the job_id to check status and retrieve results."
        }
        
    except Exception as e:
        logger.error("Failed to submit async chat job", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to submit job: {str(e)}"
        )


@router.get("/status/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """
    Get the status of an asynchronous job.
    
    Returns current status, progress, and timing information.
    """
    try:
        status = await job_queue.get_job_status(job_id)
        
        if not status:
            raise HTTPException(
                status_code=404,
                detail="Job not found"
            )
        
        return JobStatusResponse(**status)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get job status", job_id=job_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get job status: {str(e)}"
        )


@router.get("/result/{job_id}", response_model=JobResultResponse)
async def get_job_result(job_id: str):
    """
    Get the result of a completed job.
    
    Returns the job result if completed, or current status if still processing.
    """
    try:
        # First check if job is completed
        result = await job_queue.get_job_result(job_id)
        
        if result:
            # Job queue now returns flattened structure with all fields
            return JobResultResponse(**result)
        
        # If not completed, return current status
        status = await job_queue.get_job_status(job_id)
        
        if not status:
            raise HTTPException(
                status_code=404,
                detail="Job not found"
            )
        
        return JobResultResponse(
            job_id=job_id,
            status=status["status"],
            response=None,
            completed_at=None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get job result", job_id=job_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get job result: {str(e)}"
        )


@router.delete("/cancel/{job_id}")
async def cancel_job(job_id: str):
    """
    Cancel a pending or processing job.
    
    Note: Jobs that are already completed cannot be cancelled.
    """
    try:
        # Get current job status
        status = await job_queue.get_job_status(job_id)
        
        if not status:
            raise HTTPException(
                status_code=404,
                detail="Job not found"
            )
        
        if status["status"] in ["completed", "failed", "cancelled"]:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot cancel job with status: {status['status']}"
            )
        
        # Update job status to cancelled
        await job_queue.update_job_progress(job_id, 0, JobStatus.CANCELLED)
        
        logger.info("Job cancelled", job_id=job_id)
        
        return {
            "job_id": job_id,
            "status": "cancelled",
            "message": "Job cancelled successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to cancel job", job_id=job_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to cancel job: {str(e)}"
        )


@router.get("/jobs")
async def list_jobs(limit: int = 10, status: Optional[str] = None):
    """
    List recent jobs (for debugging/monitoring).
    
    Note: In production, this should be restricted to admin users.
    """
    try:
        # This is a simplified implementation
        # In production, you'd want proper filtering and pagination
        jobs = []
        
        for job_id, job in list(job_queue.jobs.items())[-limit:]:
            if status and job.status.value != status:
                continue
                
            jobs.append({
                "job_id": job_id,
                "status": job.status.value,
                "created_at": job.created_at.isoformat(),
                "progress": job.progress
            })
        
        return {
            "jobs": jobs,
            "total": len(jobs)
        }
        
    except Exception as e:
        logger.error("Failed to list jobs", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list jobs: {str(e)}"
        )


@router.get("/stats")
async def get_job_stats():
    """
    Get job queue statistics (for monitoring).
    
    Note: In production, this should be restricted to admin users.
    """
    try:
        stats = await job_queue.get_job_stats()
        return stats
        
    except Exception as e:
        logger.error("Failed to get job stats", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get job stats: {str(e)}"
        )


def _determine_job_type(message: str) -> str:
    """
    Determine job type based on message content.
    """
    message_lower = message.lower()
    
    if any(keyword in message_lower for keyword in ["prior art", "patent search", "search patents"]):
        return "prior_art_search"
    elif any(keyword in message_lower for keyword in ["draft", "claim", "patent claim"]):
        return "claim_drafting"
    elif any(keyword in message_lower for keyword in ["analyze", "analysis", "review"]):
        return "claim_analysis"
    elif any(keyword in message_lower for keyword in ["search", "find", "look up"]):
        return "web_search"
    else:
        return "general_chat"
