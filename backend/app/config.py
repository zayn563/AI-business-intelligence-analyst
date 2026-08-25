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
# SETTINGS
# ============================================================

class Settings(BaseSettings):

    # --------------------------------------------------------
    # PostgreSQL
    # --------------------------------------------------------

    db_host: str
    db_port: int = 5432
    db_name: str
    db_user: str
    db_password: str


    # --------------------------------------------------------
    # Google Sheets
    # --------------------------------------------------------

    google_service_account_file: str | None = None


    # --------------------------------------------------------
    # LOCAL LLM
    # --------------------------------------------------------

    llm_provider: str = "ollama"

    ollama_base_url: str = (
        "http://127.0.0.1:11434"
    )

    ollama_model: str = (
        "qwen3:4b"
    )


    # --------------------------------------------------------
    # ANALYST PERFORMANCE
    # --------------------------------------------------------

    # If the deterministic parser is this confident or
    # higher, Ollama is not called.
    analyst_fast_path_confidence: float = 0.75

    # Routine answers should use deterministic business
    # response composition.
    #
    # Ollama response rewriting is deliberately disabled
    # because:
    #
    # 1. deterministic answers are already business-ready;
    # 2. it removes a second LLM call;
    # 3. it materially improves local performance;
    # 4. it prevents unnecessary hallucination risk.
    #
    # This can later be enabled for an optional
    # "Explain with AI" button in the frontend.
    analyst_use_llm_response: bool = False


    # --------------------------------------------------------
    # ENVIRONMENT CONFIGURATION
    # --------------------------------------------------------

    model_config = SettingsConfigDict(
        env_file=
            ROOT
            /
            ".env",

        env_file_encoding=
            "utf-8",

        extra=
            "ignore",
    )


# ============================================================
# SETTINGS INSTANCE
# ============================================================

settings = Settings()