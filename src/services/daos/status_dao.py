from asyncio import new_event_loop, AbstractEventLoop
from datetime import datetime
from typing import Any

from sqlalchemy import Table, insert, desc, CursorResult, Row, select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, AsyncConnection

from database.tables import jobs_table, JobStatus
from src.models.dto_data_classes.status_dto import JobsDTO


class JobsDAO:
    def __init__(self, connection_string: str) -> None:
        self._engine: AsyncEngine = create_async_engine(connection_string)
        self._table: Table = jobs_table

    async def read_status(self, job_id: str) -> JobsDTO | None:
        """
        Gets the job status

        SELECT
            id,
            jobs_id,
            user_id,
            raw_search_results_id,
            job_status,
            created_at
        FROM jobs
        WHERE jobs_id = :jobs_id
        ORDER BY created_at DESC
        LIMIT 1
        """
        async with self._engine.begin() as conn:
            cursor_result: CursorResult = await conn.execute(
                select(
                    self._table.c.id,
                    self._table.c.jobs_id,
                    self._table.c.user_id,
                    self._table.c.raw_search_results_id,
                    self._table.c.job_status,
                    self._table.c.created_at,
                )
                .where(self._table.c.jobs_id == job_id)
                .order_by(desc(self._table.c.created_at))
                .limit(1)
            )
            # text_clause: TextClause = text(
            #     """
            #     SELECT
            #         id,
            #         jobs_id,
            #         user_id,
            #         raw_search_results_id,
            #         job_status,
            #         created_at
            #     FROM jobs
            #     WHERE jobs_id =:jobs_id
            #     ORDER BY created_at
            #     DESC LIMIT 1
            #     """
            # )
            # cursor_result: CursorResult = await conn.execute(text_clause, {
            #     "jobs_id": job_id
            # })
        row: Row | None = cursor_result.fetchone()
        deserialized_row: JobsDTO | None = (
            JobsDTO(
                id=row[0],
                jobs_id=row[1],
                user_id=row[2],
                raw_search_results_id=row[3],
                job_status=JobStatus(row[4]),
                created_at=row[5],
            )
            if row is not None
            else None
        )
        return deserialized_row

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


if __name__ == "__main__":
    dao: JobsDAO = JobsDAO(
        connection_string="postgresql+asyncpg://localhost:5432/yahoo_search_engine_rt"
    )
    event_loop: AbstractEventLoop = new_event_loop()
    jobs_dto: JobsDTO | None = event_loop.run_until_complete(
        dao.read_status(job_id="6883d0f0-ecf6-4849-bc0a-a6ab1dedfa71")
    )
    print(jobs_dto)
