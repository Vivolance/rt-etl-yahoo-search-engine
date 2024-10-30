"""
conftest.py

Contains fixture(reusable components for your unit/integration test) common to all tests

In this case, we don't have any shared fixture
"""

import toml
from typing import Any


def integration_test_db_config() -> dict[str, Any]:
    return toml.load("integration_tests/config.toml")["database"]
