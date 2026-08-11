import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI


# ============================================================
# PROJECT ENVIRONMENT
# ============================================================

ROOT = (
    Path(__file__)
    .resolve()
    .parents[3]
)

ENV_FILE = (
    ROOT
    /
    ".env"
)

load_dotenv(
    dotenv_path=ENV_FILE,
    override=False,
)


# ============================================================
# SETTINGS
# ============================================================

def get_openai_api_key() -> str:

    return (
        os.getenv(
            "OPENAI_API_KEY",
            ""
        )
        .strip()
    )


def get_openai_model() -> str:

    return (
        os.getenv(
            "OPENAI_MODEL",
            "gpt-5-mini",
        )
        .strip()
    )


def llm_available() -> bool:

    return bool(
        get_openai_api_key()
    )


# ============================================================
# CLIENT
# ============================================================

def get_openai_client() -> OpenAI:

    api_key = (
        get_openai_api_key()
    )

    if not api_key:

        raise RuntimeError(
            "OPENAI_API_KEY is not configured."
        )

    return OpenAI(
        api_key=api_key
    )