from sqlalchemy import Table, insert
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine

from database.tables import jobs_table
from src.models.status_dto import StatusDTO


class StatusDAO:
    def __init__(self, connection_string: str) -> None:
        self._engine: AsyncEngine = create_async_engine(connection_string)
        self._table: Table = jobs_table

    async def insert_status(self, input: StatusDTO) -> None:
        input_dict: dict[str, str] = input.model_dump()
        async with self._engine.begin() as conn:
            await conn.execute(insert(self._table), [input_dict])
