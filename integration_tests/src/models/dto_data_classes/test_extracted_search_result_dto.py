from datetime import datetime
from uuid import UUID

import pytest
from src.models.dto_data_classes.extracted_search_result_dto import (
    ExtractedSearchResultDTO,
)
from src.models.extractor_data_classes.extracted_search_result import (
    ExtractedSearchResult,
)


dummy_uuid: UUID = UUID("12345678123456781234567812345678")


class TestExtractedSearchResultDTO:
    @pytest.mark.parametrize(
        ["search_result", "jobs_id", "expected_result"],
        [
            [
                ExtractedSearchResult(
                    id=str(dummy_uuid),
                    user_id="test_user_id",
                    url="http://example.com",
                    date="2024-01-01",
                    body="Test body content",
                    created_at=datetime(2024, 10, 1, 12, 0, 0),
                ),
                "test_jobs_id",
                ExtractedSearchResultDTO(
                    id=str(dummy_uuid),
                    jobs_id="test_jobs_id",
                    user_id="test_user_id",
                    url="http://example.com",
                    date="2024-01-01",
                    body="Test body content",
                    created_at=datetime(2024, 10, 1, 12, 0, 0),
                ),
            ],
            [
                ExtractedSearchResult(
                    id=str(dummy_uuid),
                    user_id="test_user_id",
                    url="http://example.com",
                    date="2024-01-01",
                    body=None,
                    created_at=datetime(2024, 10, 1, 12, 0, 0),
                ),
                "test_jobs_id",
                ExtractedSearchResultDTO(
                    id=str(dummy_uuid),
                    jobs_id="test_jobs_id",
                    user_id="test_user_id",
                    url="http://example.com",
                    date="2024-01-01",
                    body=None,
                    created_at=datetime(2024, 10, 1, 12, 0, 0),
                ),
            ],
        ],
    )
    def test_from_search_results(
        self,
        search_result: ExtractedSearchResult,
        jobs_id: str,
        expected_result: ExtractedSearchResultDTO,
    ) -> None:
        # Act
        extracted_search_result_dto = ExtractedSearchResultDTO.from_search_results(
            search_result, jobs_id
        )

        # Assert
        assert extracted_search_result_dto == expected_result
