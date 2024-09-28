from asyncio import new_event_loop, AbstractEventLoop
from typing import Sequence

from sqlalchemy import insert, Table, CursorResult, select, desc, Row
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine, AsyncConnection

from database.tables import extracted_search_results_table
from src.models.dto_data_classes.extracted_search_result_dto import (
    ExtractedSearchResultDTO,
)


class ExtractedSearchResultsDAO:
    def __init__(self, connection_string: str) -> None:
        self._engine: AsyncEngine = create_async_engine(connection_string)
        self._table: Table = extracted_search_results_table

    async def fetch(self, jobs_id: str) -> list[ExtractedSearchResultDTO]:
        """
        SELECT
            id,
            jobs_id,
            url,
            date,
            body,
            created_at
        FROM extracted_search_results
        WHERE jobs_id = :jobs_id
        ORDER BY created_at DESC
        """
        async with self._engine.begin() as conn:
            cursor_result: CursorResult = await conn.execute(
                select(
                    extracted_search_results_table.c.id,
                    extracted_search_results_table.c.jobs_id,
                    extracted_search_results_table.c.user_id,
                    extracted_search_results_table.c.url,
                    extracted_search_results_table.c.date,
                    extracted_search_results_table.c.body,
                    extracted_search_results_table.c.created_at,
                )
                .where(extracted_search_results_table.c.jobs_id == jobs_id)
                .order_by(desc(extracted_search_results_table.c.created_at))
            )
        rows: Sequence[Row] = cursor_result.fetchall()
        deserialized_results: list[ExtractedSearchResultDTO] = [
            ExtractedSearchResultDTO(
                id=row[0],
                jobs_id=row[1],
                user_id=row[2],
                url=row[3],
                date=row[4],
                body=row[5],
                created_at=row[6],
            )
            for row in rows
        ]
        return deserialized_results

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


if __name__ == "__main__":
    dao: ExtractedSearchResultsDAO = ExtractedSearchResultsDAO(
        connection_string="postgresql+asyncpg://localhost:5432/yahoo_search_engine_rt"
    )
    event_loop: AbstractEventLoop = new_event_loop()
    results: list[ExtractedSearchResultDTO] = event_loop.run_until_complete(
        dao.fetch(jobs_id="6883d0f0-ecf6-4849-bc0a-a6ab1dedfa71")
    )
    print(results)
