from datetime import datetime
from uuid import UUID

import pytest
from freezegun import freeze_time
from unittest.mock import patch
from src.models.dto_data_classes.raw_search_results_dto import RawSearchResultsDTO


dummy_uuid: UUID = UUID("12345678123456781234567812345678")


class TestRawSearchResultsDTO:
    @pytest.mark.parametrize(
        ["user_id", "search_term", "result", "expected_result"],
        [
            [
                "dummy_user_id",
                "starbucks",
                "Matcha Latte",
                RawSearchResultsDTO(
                    id=str(dummy_uuid),
                    user_id="dummy_user_id",
                    search_term="starbucks",
                    result="Matcha Latte",
                    created_at=datetime(year=2024, month=10, day=1, hour=12),
                ),
            ],
            [
                "dummy_user_id",
                "starbucks",
                None,
                RawSearchResultsDTO(
                    id=str(dummy_uuid),
                    user_id="dummy_user_id",
                    search_term="starbucks",
                    result=None,
                    created_at=datetime(year=2024, month=10, day=1, hour=12),
                ),
            ],
        ],
    )
    def test_create(
        self,
        user_id: str,
        search_term: str,
        result: str | None,
        expected_result: RawSearchResultsDTO,
    ) -> None:
        # freezetime to freeze the actual create method with datetime.utcnow()
        with freeze_time("2024-10-1 12:00:00"), patch(
            "src.models.dto_data_classes.raw_search_results_dto.uuid.uuid4",
            return_value=dummy_uuid,
        ):
            raw_search_results_dto: RawSearchResultsDTO = RawSearchResultsDTO.create(
                user_id=user_id, search_term=search_term, result=result
            )
            assert raw_search_results_dto == expected_result
