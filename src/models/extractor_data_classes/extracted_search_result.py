import uuid
from datetime import datetime

from pydantic import BaseModel

from src.models.extractor_data_classes.extracted_text_group import ExtractedTextGroup


class ExtractedSearchResult(BaseModel):
    """
    Represents a single extracted search result.
    This data class is implemented using pydantic BaseModel.
    """

    id: str
    user_id: str
    url: str | None
    date: str | None
    body: str | None
    created_at: datetime

    @staticmethod
    def from_extracted_text_group(
        user_id: str,
        text_group: ExtractedTextGroup,
    ) -> "ExtractedSearchResult":
        """
        Smart constructor to create a single search result from ExtractedTextGroup
        """
        return ExtractedSearchResult(
            id=str(uuid.uuid4()),
            user_id=user_id,
            url=text_group.link_str,
            date=text_group.date_str,
            body=text_group.body_str,
            created_at=datetime.utcnow(),
        )

    @staticmethod
    def create_search_result(
        user_id: str, url: str | None, date: str | None, body: str | None
    ) -> "ExtractedSearchResult":
        """
        Smart constructor to create a search result
        """
        return ExtractedSearchResult(
            id=str(uuid.uuid4()),
            user_id=user_id,
            url=url,
            date=date,
            body=body,
            created_at=datetime.utcnow(),
        )
