import uuid
from datetime import datetime

from pydantic import BaseModel, field_serializer

from database.tables import JobStatus


class JobsDTO(BaseModel):
    """
    id is unique

    we can have multiple rows with the same jobs_id
    - PIT style; an update is an insert
    """

    id: str
    jobs_id: str
    user_id: str
    raw_search_results_id: str | None
    job_status: JobStatus
    created_at: datetime

    @staticmethod
    def create_job(user_id: str) -> "JobsDTO":
        return JobsDTO(
            id=str(uuid.uuid4()),
            jobs_id=str(uuid.uuid4()),
            user_id=user_id,
            raw_search_results_id=None,
            job_status=JobStatus.IN_PROGRESS,
            created_at=datetime.utcnow(),
        )

    @staticmethod
    def create_completed_job(
        jobs_id: str,
        user_id: str,
        raw_search_results_id: str,
    ) -> "JobsDTO":
        return JobsDTO(
            id=str(uuid.uuid4()),
            jobs_id=jobs_id,
            user_id=user_id,
            raw_search_results_id=raw_search_results_id,
            job_status=JobStatus.COMPLETED,
            created_at=datetime.utcnow(),
        )

    @field_serializer("job_status")
    def serialize_job_status(self, job_status: JobStatus) -> str:
        return job_status.value

    @field_serializer("created_at")
    def serialize_created_at(self, created_at: datetime) -> str:
        return created_at.strftime("%Y-%m-%dT%H:%M:%S")
