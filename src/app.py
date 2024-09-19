from aiohttp.web import Application
from aiohttp.web import get
from aiohttp import web

from aiohttp.web_routedef import post

from src.router import Router
from src.services.status_dao import StatusDAO

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
