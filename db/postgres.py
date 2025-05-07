"""Postgresql database implementation."""

from prettyconf import config
from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

url = "postgresql+asyncpg://postgres:postgres@db:5432/report_siem"
postgres_url = config("POSTGRES_URL", default=url)
postgres_schema = config("POSTGRES_SCHEMA")

async_engine = create_async_engine(postgres_url, future=True, pool_pre_ping=True)  # NOQA

SessionLocal = sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

Base = declarative_base(metadata=MetaData(schema=postgres_schema))
