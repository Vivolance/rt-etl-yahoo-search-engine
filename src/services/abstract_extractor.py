from abc import ABC, abstractmethod

from src.models.extractor_data_classes.extracted_search_result import (
    ExtractedSearchResult,
)


class SearchResultExtractor(ABC):
    @abstractmethod
    def extract(self, html: str, user_id: str) -> list[ExtractedSearchResult]:
        raise NotImplementedError("Not Implemented")
