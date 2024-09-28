from pydantic import BaseModel, field_serializer

from database.tables import JobStatus


class ResponseStatus(BaseModel):
    job_id: str
    status: JobStatus

    @field_serializer("status")
    def serialize_status(self, input_status: JobStatus) -> str:
        return input_status.value
