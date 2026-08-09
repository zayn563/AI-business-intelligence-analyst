from pathlib import Path
import os

import psycopg
from dotenv import load_dotenv


# ============================================================
# PATHS
# ============================================================

ROOT = Path(__file__).resolve().parents[1]

ENV_FILE = ROOT / ".env"

SCHEMA_FILE = ROOT / "database" / "schema.sql"


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv(ENV_FILE)


DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT"),
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
}


def main():

    print("\nConnecting to PostgreSQL...")

    with psycopg.connect(**DB_CONFIG) as connection:

        print("Connected successfully.")

        schema_sql = SCHEMA_FILE.read_text(
            encoding="utf-8"
        )

        with connection.cursor() as cursor:

            cursor.execute(schema_sql)

        connection.commit()

        print("Schema created successfully.")

        # --------------------------------------------
        # Validate tables
        # --------------------------------------------

        with connection.cursor() as cursor:

            cursor.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'analytics'
                ORDER BY table_name;
            """)

            tables = cursor.fetchall()

        print("\nTables created:")

        for table in tables:
            print(f"  - {table[0]}")

        print(
            f"\nTotal tables: {len(tables)}"
        )


if __name__ == "__main__":
    main()