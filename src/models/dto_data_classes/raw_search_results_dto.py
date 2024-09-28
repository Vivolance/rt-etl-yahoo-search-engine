import uuid
from datetime import datetime

from pydantic import BaseModel


class RawSearchResultsDTO(BaseModel):
    id: str
    user_id: str
    search_term: str
    result: str | None
    created_at: datetime

    @staticmethod
    def create(
        user_id: str, search_term: str, result: str | None
    ) -> "RawSearchResultsDTO":
        return RawSearchResultsDTO(
            id=str(uuid.uuid4()),
            user_id=user_id,
            search_term=search_term,
            result=result,
            created_at=datetime.utcnow(),
        )
