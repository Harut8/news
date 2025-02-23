import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

from src.core.conf.settings import SETTINGS
from src.core.db.pg_base_model import PgBaseModel
from src.app.crawler.model import Url, Index, Content, Meta, Author
from src.app.scheduler.model import Scheduler

config = context.config


if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = PgBaseModel.metadata

config.set_main_option("sqlalchemy.url", SETTINGS.DATABASE.DATABASE_URL)


def exclude_tables_from_config(config_):
    tables_ = config_.get("tables", None)
    if tables_ is not None:
        tables = tables_.split(",")
    return tables


exclude_tables = config.get_section("alembic:exclude").get("tables", "").split(",")


def include_object(object, name, type_, *args, **kwargs):
    return not (type_ == "table" and name in exclude_tables)


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        include_object=include_object,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        include_object=include_object,
        include_schemas=False,
        target_metadata=target_metadata,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        # await connection.execute(text("SET lock_timeout = '4s'"))
        # await connection.execute(text("SET statement_timeout = '8s'"))
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""

    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

