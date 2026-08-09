from pathlib import Path

from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)


# ============================================================
# PROJECT ROOT
# ============================================================

ROOT = (
    Path(__file__)
    .resolve()
    .parents[2]
)


# ============================================================
# APPLICATION SETTINGS
# ============================================================

class Settings(BaseSettings):

    db_host: str
    db_port: int = 5432
    db_name: str
    db_user: str
    db_password: str

    model_config = SettingsConfigDict(
        env_file=ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


# ============================================================
# SETTINGS INSTANCE
#
# database.py imports THIS object.
# ============================================================

settings = Settings()