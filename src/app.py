from typing import Any

from aiohttp.web import Application
from aiohttp.web import get
from aiohttp import web

from aiohttp.web_routedef import post
import toml
from src.router import Router
from src.services.status_dao import JobsDAO

if __name__ == "__main__":
    app: Application = Application()

    config: dict[str, Any] = toml.load("src/config/config.toml")
    pg_config: dict[str, Any] = config["postgres"]
    producer_config: dict[str, str] = config["kafka"]["producer"]["server"]
    formatted_producer_config: dict[str, Any] = {
        key.replace("_", "."): value for key, value in producer_config.items()
    }
    print(formatted_producer_config)
    connection_string: str = pg_config["connection_string"]
    status_dao: JobsDAO = JobsDAO(connection_string)
    router: Router = Router(status_dao, formatted_producer_config)
    app.add_routes(
        [
            post("/search", router.search),
            get("/status", router.status),
            get("/result", router.result),
        ]
    )
    web.run_app(app, host="0.0.0.0", port=8000)
