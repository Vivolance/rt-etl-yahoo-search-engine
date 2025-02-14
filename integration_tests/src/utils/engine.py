from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
import toml
from typing import Any

from src.utils.construct_connection_string import (
    construct_sqlalchemy_url_from_db_config,
)

dummy_uuid: UUID = UUID("12345678123456781234567812345678")

db_config: dict[str, Any] = toml.load("integration_tests/config.toml")["database"]

engine: AsyncEngine = create_async_engine(
    construct_sqlalchemy_url_from_db_config(db_config, use_async_pg=True)
)
