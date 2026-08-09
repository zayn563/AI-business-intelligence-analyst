from pathlib import Path
import os

import psycopg
from dotenv import load_dotenv


# ============================================================
# PROJECT PATHS
# ============================================================

ROOT = (
    Path(__file__)
    .resolve()
    .parents[1]
)

ENV_FILE = ROOT / ".env"

SQL_FILE = (
    ROOT
    / "database"
    / "live_pipeline.sql"
)


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv(
    dotenv_path=ENV_FILE,
    override=True,
)


DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": int(
        os.getenv(
            "DB_PORT",
            5432,
        )
    ),
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
}


# ============================================================
# MAIN
# ============================================================

def main():

    print(
        "\n============================================"
    )

    print(
        "INITIALIZING LIVE DATA PIPELINE"
    )

    print(
        "============================================"
    )


    if not SQL_FILE.exists():

        raise FileNotFoundError(
            f"SQL file not found: "
            f"{SQL_FILE}"
        )


    sql = SQL_FILE.read_text(
        encoding="utf-8"
    )


    print(
        "\nConnecting to PostgreSQL..."
    )


    with psycopg.connect(
        **DB_CONFIG
    ) as connection:

        with connection.cursor() as cursor:

            cursor.execute(
                sql
            )


            cursor.execute(
                """
                SELECT
                    table_name
                FROM information_schema.tables
                WHERE
                    table_schema = 'analytics'
                    AND table_name IN (
                        'data_sources',
                        'source_column_mappings',
                        'data_refresh_runs',
                        'source_record_state'
                    )
                ORDER BY table_name;
                """
            )


            tables = [
                row[0]
                for row
                in cursor.fetchall()
            ]


    print(
        "\nLive pipeline tables:"
    )


    for table in tables:

        print(
            f"- {table}"
        )


    print(
        "\nLive pipeline initialized successfully."
    )


if __name__ == "__main__":

    main()