from datetime import datetime

from pydantic import BaseModel, field_serializer


class RawSearchResultsRecord(BaseModel):
    user_id: str
    search_term: str
    job_id: str
    job_created_at: datetime
    raw_search_results_id: str
    raw_search_at: datetime

    @field_serializer("job_created_at")
    def serialize_job_created_at(self, value: datetime) -> str:
        return value.strftime("%Y-%m-%d %H:%M:%S")

    @field_serializer("raw_search_at")
    def serialize_raw_search_at(self, value: datetime) -> str:
        return value.strftime("%Y-%m-%d %H:%M:%S")
