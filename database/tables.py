from enum import Enum

from sqlalchemy import (
    MetaData,
    Table,
    Text,
    DateTime,
    ForeignKey,
    Column,
    Enum as SQLAlchemyEnum,
)


metadata: MetaData = MetaData()


class JobStatus(Enum):
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"


"""
CREATE TABLE users(
    user_id TEXT PRIMARY KEY,
    created_at TIMESTAMP NOT NULL
)
"""
user_table: Table = Table(
    "users",
    metadata,
    Column("id", Text, primary_key=True),
    Column("created_at", DateTime, nullable=False),
)

"""
CREATE TABLE raw_search_results(
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    search_term TEXT NOT NULL,
    result TEXT,
    created_at TIMESTAMP NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
)
"""
raw_search_result_table: Table = Table(
    "raw_search_results",
    metadata,
    Column("id", Text, primary_key=True),
    Column("user_id", Text, ForeignKey("users.id"), nullable=False),
    Column("search_term", Text, nullable=False),
    Column("result", Text, nullable=True),
    Column("created_at", DateTime, nullable=False),
)

"""
CREATE TABLE extracted_search_results(
    id TEXT PRIMARY KEY,
    jobs_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    url TEXT,
    date TEXT,
    body TEXT,
    created_at TIMESTAMP NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id),
)
"""
extracted_search_results_table: Table = Table(
    "extracted_search_results",
    metadata,
    Column("id", Text, primary_key=True),
    Column("jobs_id", Text, nullable=False),
    Column("user_id", Text, ForeignKey("users.id"), nullable=False),
    Column("url", Text, nullable=True),
    Column("date", Text, nullable=True),
    Column("body", Text, nullable=True),
    Column("created_at", DateTime, nullable=False),
)

"""
CREATE TABLE jobs(
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    raw_search_results_id TEXT,
    job_status EnumType NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (extracted_search_results_id) REFERENCES extracted_search_results(id),
    FOREIGN KEY (search_id) REFERENCES search_results(id)
)
"""
jobs_table: Table = Table(
    "jobs",
    metadata,
    Column("id", Text, primary_key=True),
    Column("jobs_id", Text, nullable=False),
    Column("user_id", Text, ForeignKey("users.id"), nullable=False),
    Column(
        "raw_search_results_id",
        Text,
        ForeignKey("raw_search_results.id"),
        nullable=True,
    ),
    Column("job_status", SQLAlchemyEnum(JobStatus), nullable=False),
    Column("created_at", DateTime, nullable=False),
)
