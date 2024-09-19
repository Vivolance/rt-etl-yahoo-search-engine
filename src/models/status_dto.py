import uuid

from pydantic import BaseModel, field_serializer

from database.tables import JobStatus


class StatusDTO(BaseModel):
    id: str
    user_id: str
    raw_search_results_id: str | None
    extracted_search_results_id: str | None
    job_status: JobStatus

    @staticmethod
    def new(user_id: str) -> "StatusDTO":
        return StatusDTO(
            id=str(uuid.uuid4()),
            user_id=user_id,
            raw_search_results_id=None,
            extracted_search_results_id=None,
            job_status=JobStatus.IN_PROGRESS,
        )

    @field_serializer("job_status")
    def serialize_job_status(self, job_status: JobStatus) -> str:
        return job_status.value
