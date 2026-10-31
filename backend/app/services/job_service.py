"""
Privacy Eye — Real-Time Analysis Job Tracker (Phase 4)
Exposes real job states (queued, processing, stage name, completed, failed, error)
derived from actual execution points in the pipeline without artificial client-side timers.
"""
import time
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timezone
import structlog

logger = structlog.get_logger(__name__)

JOB_QUEUED = "queued"
JOB_PROCESSING = "processing"
JOB_COMPLETED = "completed"
JOB_FAILED = "failed"


@dataclass
class AnalysisJob:
    job_id: str
    user_id: str
    media_type: str
    filename: str
    status: str = JOB_QUEUED  # queued | processing | completed | failed
    stage: str = "QUEUED"
    stage_name: str = "Job queued for forensic ingestion"
    error: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "status": self.status,
            "stage": self.stage,
            "stage_name": self.stage_name,
            "completed": self.status == JOB_COMPLETED,
            "failed": self.status == JOB_FAILED,
            "error": self.error,
            "analysis_id": self.job_id,
            "created_at": datetime.fromtimestamp(self.created_at, tz=timezone.utc).isoformat(),
            "updated_at": datetime.fromtimestamp(self.updated_at, tz=timezone.utc).isoformat(),
        }


class JobTracker:
    def __init__(self):
        self._jobs: Dict[str, AnalysisJob] = {}

    def create_job(self, job_id: str, user_id: str, media_type: str, filename: str) -> AnalysisJob:
        job = AnalysisJob(
            job_id=job_id,
            user_id=user_id,
            media_type=media_type,
            filename=filename,
            status=JOB_QUEUED,
            stage="QUEUED",
            stage_name="Media payload received and queued",
        )
        self._jobs[job_id] = job
        return job

    def update_stage(self, job_id: str, stage: str, stage_name: str) -> Optional[AnalysisJob]:
        job = self._jobs.get(job_id)
        if not job:
            return None
        job.status = JOB_PROCESSING
        job.stage = stage
        job.stage_name = stage_name
        job.updated_at = time.time()
        logger.info("Job stage updated", job_id=job_id, stage=stage, stage_name=stage_name)
        return job

    def complete_job(self, job_id: str, result: Dict[str, Any]) -> Optional[AnalysisJob]:
        job = self._jobs.get(job_id)
        if not job:
            return None
        job.status = JOB_COMPLETED
        job.stage = "COMPLETE"
        job.stage_name = "Forensic & neural analysis complete"
        job.result = result
        job.updated_at = time.time()
        logger.info("Job completed", job_id=job_id)
        return job

    def fail_job(self, job_id: str, error: str) -> Optional[AnalysisJob]:
        job = self._jobs.get(job_id)
        if not job:
            return None
        job.status = JOB_FAILED
        job.stage = "FAILED"
        job.stage_name = "Analysis failed"
        job.error = error
        job.updated_at = time.time()
        logger.error("Job failed", job_id=job_id, error=error)
        return job

    def get_job(self, job_id: str) -> Optional[AnalysisJob]:
        return self._jobs.get(job_id)


# Global singleton instance
job_tracker = JobTracker()
