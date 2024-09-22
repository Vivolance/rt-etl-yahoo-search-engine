from sqlalchemy import insert, Table
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from database.tables import raw_search_result_table
from src.models.raw_search_results import RawSearchResults


class RawSearchResultsDAO:
    def __init__(self, connection_string: str) -> None:
        self._engine: AsyncEngine = create_async_engine(connection_string)
        self._table: Table = raw_search_result_table

    async def insert_many(self, results: list[RawSearchResults]) -> None:
        async with self._engine.begin() as conn:
            deserialized_results: list[dict[str, str]] = [
                result.model_dump() for result in results
            ]
            await conn.execute(insert(self._table), deserialized_results)
