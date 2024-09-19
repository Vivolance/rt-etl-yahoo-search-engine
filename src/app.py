from aiohttp.web import Request, Response, Application
from aiohttp.web import get
from aiohttp import web
import uuid
from typing import Any
import json

from aiohttp.web_routedef import post
from sqlalchemy import insert, Table
from pydantic import BaseModel, field_serializer
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from database.tables import jobs_table, JobStatus


class StatusDTO(BaseModel):
    id: str
    user_id: str
    raw_search_results_id: str | None
    extracted_search_results_id: str | None
    job_status: JobStatus

    @staticmethod
    def new(user_id: str) -> "StatusDTO":
        return StatusDTO(
            id=str(uuid.uuid4()),
            user_id=user_id,
            raw_search_results_id=None,
            extracted_search_results_id=None,
            job_status=JobStatus.IN_PROGRESS,
        )

    @field_serializer("job_status")
    def serialize_job_status(self, job_status: JobStatus) -> str:
        return job_status.value


class StatusDAO:
    def __init__(self, connection_string: str) -> None:
        self._engine: AsyncEngine = create_async_engine(connection_string)
        self._table: Table = jobs_table

    async def insert_status(self, input: StatusDTO) -> None:
        input_dict: dict[str, str] = input.model_dump()
        async with self._engine.begin() as conn:
            await conn.execute(insert(self._table), [input_dict])


class Router:
    def __init__(self, status_dao: StatusDAO) -> None:
        self._status_dao: StatusDAO = status_dao

    async def search(self, request: Request) -> Response:
        try:
            body: dict[str, Any] = await request.json()
        except Exception as err:
            print(f"Unable to parse body with err: {err}")
            return Response(status=500, text=f"Unable to parse body with err: {err}")

        # validation of client payload
        search_term: str | None = body.get("search_term")
        if search_term is None:
            return Response(status=400, text="Search term is empty")
        user_id: str | None = body.get("user_id")
        if user_id is None:
            return Response(status=400, text="User id is empty")

        # Step 1: Save job id into Postgres
        status_dto: StatusDTO = StatusDTO.new(user_id=user_id)
        await self._status_dao.insert_status(status_dto)
        response_body: dict[str, Any] = {
            "job_id": status_dto.id,
            "search_term": search_term,
        }
        serialized_body = json.dumps(response_body)
        return Response(text=serialized_body)

    async def status(self, request: Request) -> Response:
        body: dict[str, Any] = {"status": "In Progress"}
        serialized_body = json.dumps(body)
        return Response(text=serialized_body)

    async def result(self, request: Request) -> Response:
        body: dict[str, Any] = {"result": [{"title": "Coffee Bean is the best"}]}
        serialized_body = json.dumps(body)
        return Response(text=serialized_body)


if __name__ == "__main__":
    app: Application = Application()
    status_dao: StatusDAO = StatusDAO(
        "postgresql+asyncpg://localhost:5432/yahoo_search_engine_rt"
    )
    router: Router = Router(status_dao)
    app.add_routes(
        [
            post("/search", router.search),
            get("/status", router.status),
            get("/result", router.result),
        ]
    )
    web.run_app(app, host="0.0.0.0", port=8000)
