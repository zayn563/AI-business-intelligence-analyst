from sqlalchemy import (
    create_engine,
    text,
)

from sqlalchemy.engine import URL

from .config import settings


# ============================================================
# DATABASE URL
# ============================================================

DATABASE_URL = URL.create(
    drivername="postgresql+psycopg",
    username=settings.db_user,
    password=settings.db_password,
    host=settings.db_host,
    port=settings.db_port,
    database=settings.db_name,
)


# ============================================================
# DATABASE ENGINE
# ============================================================

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)


# ============================================================
# DATABASE HEALTH CHECK
# ============================================================

def test_database_connection():

    with engine.connect() as connection:

        result = connection.execute(
            text(
                """
                SELECT
                    current_database(),
                    current_user;
                """
            )
        )

        row = result.fetchone()

        return {
            "database": row[0],
            "user": row[1],
        }