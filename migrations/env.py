import asyncio
from logging.config import fileConfig

from alembic.script import ScriptDirectory
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import AsyncEngine

from models.report import Report
from models.report_type import ReportType

from db.postgres import Base, postgres_url
from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.

config.set_main_option("sqlalchemy.url", postgres_url)


# Creation of the function for alembic to create the file name in
# the sequence of 0001 ... 9999
# DOC: https://alembic.sqlalchemy.org/en/latest/api/autogenerate.html#customizing-revision-generation
def process_revision_directives(cont, revision, directives):
    # extract Migration
    migration_script = directives[0]
    # extract current head revision
    head_revision = ScriptDirectory.from_config(
        cont.config).get_current_head()

    if head_revision is None:
        # edge case with first migration
        new_rev_id = 1
    else:
        # default branch with incrementation
        last_rev_id = int(head_revision.lstrip('0'))
        new_rev_id = last_rev_id + 1
    # fill zeros up to 4 digits: 1 -> 0001

    migration_script.rev_id = '{0:04}'.format(new_rev_id)


def include_name(name, type_, parent_names):
    """
    Exclude all DB namespaces from the autogenerate process, except the ones defined in the model's Metadata object.
    Can be customized to include "public" or any other namespace that alembic needs to keep track of.
    DOC: https://alembic.sqlalchemy.org/en/latest/autogenerate.html#omitting-schema-names-from-the-autogenerate-process
    """
    if type_ == "schema":
        return name in [target_metadata.schema]
    else:
        return True


def run_migrations_offline():
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        process_revision_directives=process_revision_directives,
        version_table_schema=target_metadata.schema,
        include_schemas=True,
        include_name=include_name
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(connection=connection,
                      target_metadata=target_metadata,
                      process_revision_directives=process_revision_directives,
                      compare_type=True,
                      version_table_schema=target_metadata.schema,
                      include_schemas=True,
                      include_name=include_name
        )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = AsyncEngine(
        engine_from_config(
            config.get_section(config.config_ini_section),
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
            future=True,

        )
    )

    async with connectable.connect() as connection:
        await connection.run_sync(
            do_run_migrations,)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
