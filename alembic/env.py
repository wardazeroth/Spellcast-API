import sys
import os
from sqlalchemy import MetaData

# Primero agregamos la raíz del proyecto para que python encuentre 'app'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
load_dotenv()  # Carga variables .env

from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

from app.integrations.alchemy import Base
import app.models.models
# from app.models import models

config = context.config

DATABASE_URL = os.getenv("DATABASE_URL")
print("DATABASE_URL:", DATABASE_URL)  # DEBUG: verificar que se carga bien

config.set_main_option("sqlalchemy.url", DATABASE_URL)

fileConfig(config.config_file_name)

target_metadata = Base.metadata

def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()
        
def include_object(object, name, type_, reflected, compare_to):
    # Solo incluir tablas, índices, constraints en el esquema 'spellcast'
    if name == "users" and getattr(object, "schema", None) == "auth":
        return False
    elif hasattr(object, 'schema'):
        return object.schema == "spellcast"
    return True  # para otros objetos que no tengan schema

def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            version_table_schema="spellcast",  # <-- para que la tabla alembic_version esté en ese schema
            default_schema_name="spellcast",
            include_schemas=True,
            compare_type=True,
            include_object=include_object
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
