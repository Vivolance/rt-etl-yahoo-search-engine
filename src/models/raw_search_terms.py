from datetime import datetime

from pydantic import BaseModel, field_serializer


class RawSearchTermsRecord(BaseModel):
    """
    Kafka Record to topic: `raw_search_terms`
    """

    user_id: str
    search_term: str
    job_id: str
    job_created_at: datetime

    @field_serializer("job_created_at")
    def serialize_job_created_at(self, value: datetime) -> str:
        return value.strftime("%Y-%m-%dT%H:%M:%S")
