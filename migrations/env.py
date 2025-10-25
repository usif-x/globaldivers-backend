import os
from logging.config import fileConfig

from alembic import context
from dotenv import load_dotenv
from sqlalchemy import engine_from_config, pool

# ------------------------------
# Load environment variables
# ------------------------------
load_dotenv()

# Build database URL dynamically
DB_ENGINE = os.getenv("DB_ENGINE", "postgresql")
DB_USER = os.getenv("DB_USERNAME", "postgres")
DB_PASS = os.getenv("DB_PASSWORD", "")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "topdivers")

DATABASE_URL = (
    f"{DB_ENGINE}+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# ------------------------------
# Alembic Config setup
# ------------------------------
config = context.config

# Override sqlalchemy.url from .env
config.set_main_option("sqlalchemy.url", DATABASE_URL)

# Logging setup
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

from app.core.database import Base

# ------------------------------
# Import models for autogenerate
# ------------------------------
from app.models import *

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
