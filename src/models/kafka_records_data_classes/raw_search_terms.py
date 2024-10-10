from datetime import datetime

from pydantic import BaseModel, field_serializer, field_validator


class RawSearchTermsRecord(BaseModel):
    """
    consumers Record to topic: `raw_search_terms`
    """

    user_id: str
    search_term: str
    job_id: str
    job_created_at: datetime

    @field_serializer("job_created_at")
    def serialize_job_created_at(self, value: datetime) -> str:
        return value.strftime("%Y-%m-%dT%H:%M:%S")

    @field_validator("job_created_at", mode="before")
    def deserialize_job_created_at(cls, value: str | datetime) -> datetime:
        if isinstance(value, str):
            return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S")
        return value
