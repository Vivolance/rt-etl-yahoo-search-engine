from aiohttp.web import Request, Response
from typing import Any
import json

from src.models.status_dto import StatusDTO
from src.services.status_dao import StatusDAO


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
