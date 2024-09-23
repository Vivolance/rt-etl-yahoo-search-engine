from datetime import datetime
from pydantic import BaseModel

from src.models.extractor_data_classes.extracted_search_result import (
    ExtractedSearchResult,
)


class ExtractedSearchResultDTO(BaseModel):
    id: str
    jobs_id: str
    user_id: str
    url: str | None
    date: str | None
    body: str | None
    created_at: datetime

    @staticmethod
    def from_search_results(
        search_results: ExtractedSearchResult, jobs_id: str
    ) -> "ExtractedSearchResultDTO":
        return ExtractedSearchResultDTO(
            id=search_results.id,
            jobs_id=jobs_id,
            user_id=search_results.user_id,
            url=search_results.url,
            date=search_results.date,
            body=search_results.body,
            created_at=search_results.created_at,
        )
