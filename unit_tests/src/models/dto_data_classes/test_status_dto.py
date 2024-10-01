from datetime import datetime
from uuid import UUID

import pytest
from freezegun import freeze_time
from unittest.mock import patch

from database.tables import JobStatus
from src.models.dto_data_classes.raw_search_results_dto import RawSearchResultsDTO
from src.models.dto_data_classes.status_dto import JobsDTO

dummy_uuid: UUID = UUID("12345678123456781234567812345678")
dummy_job_uuid: UUID = UUID("93283748593748568384958394975932")


class TestSatusDTO:
    @pytest.mark.parametrize(
        ["user_id", "expected_result"],
        [
            [
                "dummy_user_id",
                JobsDTO(
                    id=str(dummy_uuid),
                    jobs_id=str(dummy_job_uuid),
                    user_id="dummy_user_id",
                    raw_search_results_id=None,
                    job_status=JobStatus.IN_PROGRESS,
                    created_at=datetime(year=2024, month=10, day=1, hour=12)
                )
            ],
        ],
    )
    def test_create_job(
            self,
            user_id: str,
            expected_result: JobsDTO
    ) -> None:
        # use patch with side_effect to control generate 2 unique uuid as required.
        with freeze_time("2024-10-1 12:00:00"), patch(
                "src.models.dto_data_classes.status_dto.uuid.uuid4", side_effect=[dummy_uuid, dummy_job_uuid]
        ):
            status_dto: JobsDTO = JobsDTO.create_job(
                user_id=user_id
            )
            assert status_dto == expected_result

    @pytest.mark.parametrize(
        ["jobs_id", "user_id", "raw_search_results_id", "expected_result"],
        [
            [
                "dummy_jobs_id",
                "dummy_user_id",
                "dummy_raw_search_results_id",
                JobsDTO(
                    id=str(dummy_uuid),
                    jobs_id="dummy_jobs_id",
                    user_id="dummy_user_id",
                    raw_search_results_id="dummy_raw_search_results_id",
                    job_status=JobStatus.COMPLETED,
                    created_at=datetime(year=2024, month=10, day=1, hour=12)
                )
            ],
        ],
    )
    def test_create_completed_job(
            self,
            jobs_id: str,
            user_id: str,
            raw_search_results_id: str,
            expected_result: JobsDTO
    ) -> None:
        # use patch with side_effect to control generate 2 unique uuid as required.
        with freeze_time("2024-10-1 12:00:00"), patch(
                "src.models.dto_data_classes.status_dto.uuid.uuid4", side_effect=[dummy_uuid, dummy_job_uuid]
        ):
            status_dto: JobsDTO = JobsDTO.create_completed_job(
                jobs_id=jobs_id,
                user_id=user_id,
                raw_search_results_id=raw_search_results_id
            )
            assert status_dto == expected_result
