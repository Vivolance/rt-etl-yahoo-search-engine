from sqlalchemy import insert, Table
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine, AsyncConnection

from database.tables import extracted_search_results_table
from src.models.dtos.extracted_search_result_dto import ExtractedSearchResultDTO


class ExtractedSearchResultsDAO:
    def __init__(self, connection_string: str) -> None:
        self._engine: AsyncEngine = create_async_engine(connection_string)
        self._table: Table = extracted_search_results_table

    async def insert_many(self, results: list[ExtractedSearchResultDTO]) -> None:
        async with self._engine.begin() as conn:
            deserialized_results: list[dict[str, str]] = [
                result.model_dump() for result in results
            ]
            await conn.execute(insert(self._table), deserialized_results)

    async def insert_many_transaction(
        self, conn: AsyncConnection, results: list[ExtractedSearchResultDTO]
    ) -> None:
        deserialized_results: list[dict[str, str]] = [
            result.model_dump() for result in results
        ]
        await conn.execute(insert(self._table), deserialized_results)
