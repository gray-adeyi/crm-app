"""
Alembic environment for PostgreSQL. Local SQLite uses SQLAlchemy `create_all` + SQLite PRAGMA migrations.

From `backend/`: create revisions with `alembic revision --autogenerate -m "detail"` then `alembic upgrade head`.
"""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool

from app.core.config import get_settings
from app.core.database import Base

import app.models.entities  # noqa: F401

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata
settings = get_settings()


def run_migrations_offline() -> None:
    context.configure(url=settings.DATABASE_URL, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = create_engine(settings.DATABASE_URL, poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
