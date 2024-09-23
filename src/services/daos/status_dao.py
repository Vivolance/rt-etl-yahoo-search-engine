from datetime import datetime
from typing import Any

from sqlalchemy import Table, insert
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, AsyncConnection

from database.tables import jobs_table
from src.models.dtos.status_dto import JobsDTO


class JobsDAO:
    def __init__(self, connection_string: str) -> None:
        self._engine: AsyncEngine = create_async_engine(connection_string)
        self._table: Table = jobs_table

    async def insert_status(self, input: JobsDTO) -> None:
        """
        Used to insert and update
        - An update uploads a new row with the status being complete
        """
        input_dict: dict[str, Any] = input.model_dump()
        input_dict_created_at: datetime = datetime.strptime(
            input_dict["created_at"], "%Y-%m-%dT%H:%M:%S"
        )
        input_dict["created_at"] = input_dict_created_at
        async with self._engine.begin() as conn:
            await conn.execute(insert(self._table), [input_dict])

    async def insert_many_status_transaction(
        self, conn: AsyncConnection, input: list[JobsDTO]
    ) -> None:
        """
        Used to insert and update
        - An update uploads a new row with the status being complete
        """
        all_dicts: list[dict[str, Any]] = []
        for single_input in input:
            input_dict: dict[str, Any] = single_input.model_dump()
            input_dict_created_at: datetime = datetime.strptime(
                input_dict["created_at"], "%Y-%m-%dT%H:%M:%S"
            )
            input_dict["created_at"] = input_dict_created_at
            all_dicts.append(input_dict)
        await conn.execute(insert(self._table), all_dicts)
