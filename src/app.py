import os
from typing import Any

from aiohttp.web import Application
from aiohttp.web import get, post
from aiohttp import web
from dotenv import load_dotenv
import toml
from src.router import Router
from src.services.daos.extracted_search_results_dao import ExtractedSearchResultsDAO
from src.services.daos.status_dao import JobsDAO

load_dotenv()

if __name__ == "__main__":
    app: Application = Application()

    config: dict[str, Any] = toml.load("src/config/config.toml")
    pg_config: dict[str, Any] = config["postgres"]
    producer_config: dict[str, str] = config["kafka"]["producer"]["server"]
    # temporarily override bootstrap_servers with env var to make it work with docker
    producer_config["bootstrap_servers"] = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
    formatted_producer_config: dict[str, Any] = {
        key.replace("_", "."): value for key, value in producer_config.items()
    }
    print(formatted_producer_config)
    connection_string: str = os.getenv(
        "ASYNC_POSTGRES_URL"
    )  # pg_config["connection_string"]
    status_dao: JobsDAO = JobsDAO(connection_string)
    extracted_search_results_dao: ExtractedSearchResultsDAO = ExtractedSearchResultsDAO(
        connection_string
    )
    router: Router = Router(
        status_dao, extracted_search_results_dao, formatted_producer_config
    )
    app.add_routes(
        [
            post("/search", router.search),
            get("/status", router.status),
            get("/result", router.result),
            get("/healthcheck", router.healthcheck),
        ]
    )
    web.run_app(app, host="0.0.0.0", port=8000)
