from datetime import datetime
from unittest.mock import patch
from uuid import UUID

import pytest
from freezegun import freeze_time

from src.models.extractor_data_classes.extracted_search_result import (
    ExtractedSearchResult,
)
from src.models.extractor_data_classes.extracted_text import ExtractedText
from src.models.extractor_data_classes.extracted_text_group import ExtractedTextGroup


dummy_uuid = UUID("12345678123456781234567812345678")


class TestExtractedSearchResult:
    @pytest.mark.parametrize(
        ["user_id", "text_group", "expected_result"],
        [
            [
                "dummy_user_id",
                ExtractedTextGroup(
                    identifier="some_identifier",
                    link=[ExtractedText(parent_tags=[], text="http://example.com")],
                    body=[ExtractedText(parent_tags=[], text="Dummy body text")],
                    date=[ExtractedText(parent_tags=[], text="2024-10-1")],
                ),
                ExtractedSearchResult(
                    id=str(dummy_uuid),
                    user_id="dummy_user_id",
                    url="http://example.com",
                    date="2024-10-1",
                    body="Dummy body text",
                    created_at=datetime(year=2024, month=10, day=1, hour=12),
                ),
            ],
        ],
    )
    def test_from_extracted_text_group(
        self,
        user_id: str,
        text_group: ExtractedTextGroup,
        expected_result: ExtractedSearchResult,
    ) -> None:
        # use patch with side_effect to control generate 2 unique uuid as required.
        with freeze_time("2024-10-1 12:00:00"), patch(
            "src.models.extractor_data_classes.extracted_search_result.uuid.uuid4",
            return_value=dummy_uuid,
        ):
            extracted_search_result: ExtractedSearchResult = (
                ExtractedSearchResult.from_extracted_text_group(user_id, text_group)
            )
            assert extracted_search_result == expected_result

    @pytest.mark.parametrize(
        ["user_id", "url", "date", "body", "expected_result"],
        [
            [
                "dummy_user_id",
                "http://example.com",
                "2024-10-01",
                "dummy body",
                ExtractedSearchResult(
                    id=str(dummy_uuid),
                    user_id="dummy_user_id",
                    url="http://example.com",
                    date="2024-10-01",
                    body="dummy body",
                    created_at=datetime(year=2024, month=10, day=1, hour=12),
                ),
            ],
        ],
    )
    def test_create_search_result(
        self,
        user_id: str,
        url: str | None,
        date: str | None,
        body: str | None,
        expected_result: ExtractedSearchResult,
    ) -> None:
        # use patch with side_effect to control generate 2 unique uuid as required.
        with freeze_time("2024-10-1 12:00:00"), patch(
            "src.models.extractor_data_classes.extracted_search_result.uuid.uuid4",
            return_value=dummy_uuid,
        ):
            extracted_search_result: ExtractedSearchResult = (
                ExtractedSearchResult.create_search_result(user_id, url, date, body)
            )
            assert extracted_search_result == expected_result
