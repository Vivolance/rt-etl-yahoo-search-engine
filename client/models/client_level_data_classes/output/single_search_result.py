from datetime import datetime
from pydantic import BaseModel, field_serializer


class SingleSearchResult(BaseModel):
    id: str
    jobs_id: str
    user_id: str
    url: str | None
    date: str | None
    body: str | None
    created_at: datetime

    @field_serializer("created_at")
    def serialize_created_at(self, created_at: datetime) -> str:
        return created_at.strftime("%Y-%m-%d %H:%M%:%S")
