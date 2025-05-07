from typing import Sequence

from sqlalchemy import insert, Table, select, CursorResult, Row
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from database.tables import raw_search_result_table
from src.models.dto_data_classes.raw_search_results_dto import RawSearchResultsDTO


class RawSearchResultsDAO:
    def __init__(self, connection_string: str) -> None:
        self._engine: AsyncEngine = create_async_engine(connection_string)
        self._table: Table = raw_search_result_table

    async def insert_many(self, results: list[RawSearchResultsDTO]) -> None:
        async with self._engine.begin() as conn:
            deserialized_results: list[dict[str, str]] = [
                result.model_dump() for result in results
            ]
            # execute method takes in insert table command, and data (optional) to be inserted
            # typically in dict or [list[dict]]
            await conn.execute(insert(self._table), deserialized_results)

    async def select(self, ids: list[str]) -> list[RawSearchResultsDTO]:
        async with self._engine.begin() as conn:
            result: CursorResult = await conn.execute(
                select(
                    self._table.c.id,
                    self._table.c.user_id,
                    self._table.c.search_term,
                    self._table.c.result,
                    self._table.c.created_at,
                ).where(self._table.c.id.in_(ids))
            )
        rows: Sequence[Row] = result.fetchall()
        results: list[RawSearchResultsDTO] = [
            RawSearchResultsDTO(
                id=row[0],
                user_id=row[1],
                search_term=row[2],
                result=row[3],
                created_at=row[4],
            )
            for row in rows
        ]
        return results
