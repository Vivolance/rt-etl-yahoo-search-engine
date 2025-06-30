from datetime import datetime
from unittest.mock import patch
from uuid import UUID

import pytest
from freezegun import freeze_time

from src.services.search_result_extractor import BS4SearchResultExtractor
from src.models.extractor_data_classes.extracted_search_result import (
    ExtractedSearchResult,
)

"""
High Level: We want to test the extract method on various HTML structures.
There are 3 things that the extract method does:
1) Recursively goes through the html to find the 3 identifiers we want -> link,
body, date.
2) Filter those result groups with >= 2 identifiers with its text present.
3) Converting from list[ExtractedTextGroup] to list[ExtractedSearchResult] ->
the data structure which we want to insert into our table

Test Cases:
1) Multiple Good Search Results
2) Multiple <2 identifier results

Expected:
1) Returns the link, url, body as a ExtractedSearchResult object
2) Returns None
"""

dummy_uuid: UUID = UUID("12345678123456781234567812345678")


class TestBS4SearchResultExtractor:
    @pytest.fixture
    def extractor(self):
        return BS4SearchResultExtractor()

    @pytest.mark.parametrize(
        ("html", "expected_search_results"),
        [
            # Case 1: Multiple Search Results
            (
                """
            <div>
                <div>
                    <a href="link1">Link 1</a>
                    <span>Date 1</span>
                    <p>Body 1</p>
                </div>
                    <a href="link2">Link 2</a>
                    <span>Date 2</span>
                    <p>Body 2</p>
                </div>
            </div>
            """,
                [
                    ExtractedSearchResult(
                        id="dummy_id",
                        user_id="dummy_user_id",
                        url="link1",
                        date="Date 1",
                        body="Body 1",
                        created_at=datetime(2024, 10, 1, 12),
                    ),
                    ExtractedSearchResult(
                        id="dummy_id",
                        user_id="dummy_user_id",
                        url="link2",
                        date="Date 2",
                        body="Body 2",
                        created_at=datetime(2024, 10, 1, 12),
                    ),
                ],
            ),
            # Case 2: Multiple Search Results with some info_count < 2
            (
                """
            <div>
                <div>
                    <a href="link1">Link 1</a>
                </div>
                <div>
                    <span>Date 2</span>
                </div>
            </div>
            """,
                [],
            ),
        ],
    )
    def test_extract(
        self,
        extractor,
        html,
        expected_search_results: list[ExtractedSearchResult] | None,
    ) -> None:
        # Call the extract method with the given HTML content
        results = extractor.extract(html, "dummy_id")

        # Assertions to verify the results
        assert results == expected_search_results
