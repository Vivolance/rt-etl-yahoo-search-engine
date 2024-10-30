import pytest

from src.models.dto_data_classes.status_dto import JobsDTO


DATABASE_URL = "postgresql+asyncpg://username:password@localhost:5432/it_yahoo_search_engine_rt"


class TestJobsDAO:
    @pytest.mark.asyncio_cooperative
    async def test_read_status(self) -> JobsDTO:
        pass
