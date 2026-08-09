from pathlib import Path
import os

import psycopg
from dotenv import load_dotenv


# ------------------------------------------------------------
# PROJECT ROOT + ENV FILE
# ------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = ROOT / ".env"

print(f"Project root: {ROOT}")
print(f"ENV file: {ENV_FILE}")
print(f"ENV exists: {ENV_FILE.exists()}")


# ------------------------------------------------------------
# LOAD ENVIRONMENT VARIABLES
# ------------------------------------------------------------

load_dotenv(
    dotenv_path=ENV_FILE,
    override=True
)


db_host = os.getenv("DB_HOST")
db_port = os.getenv("DB_PORT")
db_name = os.getenv("DB_NAME")
db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")


print("\nConnection configuration:")
print(f"Host: {db_host}")
print(f"Port: {db_port}")
print(f"Database: {db_name}")
print(f"User: {db_user}")
print(f"Password loaded: {bool(db_password)}")


# ------------------------------------------------------------
# CONNECT
# ------------------------------------------------------------

print("\nAttempting PostgreSQL connection...")


try:

    with psycopg.connect(
        host=db_host,
        port=int(db_port),
        dbname=db_name,
        user=db_user,
        password=db_password,
        connect_timeout=5
    ) as connection:

        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT
                    current_database(),
                    current_user,
                    inet_server_addr(),
                    inet_server_port();
                """
            )

            result = cursor.fetchone()


        print("\nSUCCESS")
        print("-----------------------------")
        print(f"Database: {result[0]}")
        print(f"User:     {result[1]}")
        print(f"Server:   {result[2]}")
        print(f"Port:     {result[3]}")
        print("-----------------------------")

        print(
            "\nPostgreSQL connection is working correctly."
        )


except Exception as error:

    print("\nCONNECTION FAILED")
    print("-----------------------------")
    print(type(error).__name__)
    print(error)
    print("-----------------------------")

    raise