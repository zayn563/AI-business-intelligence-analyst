import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI


# ============================================================
# PROJECT PATHS
# ============================================================

# File:
# backend/app/analyst/llm_client.py
#
# parents[0] = analyst
# parents[1] = app
# parents[2] = backend
# parents[3] = project root

PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[3]
)

ENV_FILE = (
    PROJECT_ROOT
    /
    ".env"
)


# ============================================================
# LOAD ENVIRONMENT
# ============================================================

load_dotenv(
    dotenv_path=ENV_FILE,
    override=False,
)


# ============================================================
# DEFAULT SETTINGS
# ============================================================

DEFAULT_OPENAI_MODEL = (
    "gpt-5-mini"
)


# ============================================================
# API KEY
# ============================================================

def get_openai_api_key() -> str:

    """
    Return the configured OpenAI API key.

    The value is never logged or returned to API clients.
    """

    return (
        os.getenv(
            "OPENAI_API_KEY",
            "",
        )
        .strip()
    )


# ============================================================
# MODEL
# ============================================================

def get_openai_model() -> str:

    """
    Return the configured OpenAI model.

    If OPENAI_MODEL is empty, use the project's default.
    """

    configured_model = (
        os.getenv(
            "OPENAI_MODEL",
            "",
        )
        .strip()
    )

    if not configured_model:

        return (
            DEFAULT_OPENAI_MODEL
        )

    return (
        configured_model
    )


# ============================================================
# CONFIGURATION VALIDATION
# ============================================================

def get_llm_configuration_status() -> dict:

    """
    Return safe diagnostic information about the LLM
    configuration without exposing the API key.
    """

    api_key = (
        get_openai_api_key()
    )

    model = (
        get_openai_model()
    )

    issues = []


    # --------------------------------------------------------
    # API KEY VALIDATION
    # --------------------------------------------------------

    if not api_key:

        issues.append(
            "OPENAI_API_KEY is empty."
        )

    elif (
        api_key.lower()
        in {
            "your_real_openai_api_key",
            "your_openai_api_key",
            "your_api_key_here",
            "replace_me",
        }
    ):

        issues.append(
            "OPENAI_API_KEY still contains a placeholder."
        )


    # --------------------------------------------------------
    # MODEL VALIDATION
    # --------------------------------------------------------

    if not model:

        issues.append(
            "OPENAI_MODEL is empty."
        )

    elif (
        model
        in {
            "gpt",
            "gpt-",
            "openai",
            "model",
        }
    ):

        issues.append(
            (
                "OPENAI_MODEL appears incomplete or invalid. "
                "Use a valid model such as gpt-5-mini."
            )
        )


    # --------------------------------------------------------
    # STATUS
    # --------------------------------------------------------

    available = (
        len(
            issues
        )
        ==
        0
    )

    return {
        "available":
            available,

        "model":
            model,

        "api_key_configured":
            bool(
                api_key
            ),

        "environment_file":
            str(
                ENV_FILE
            ),

        "issues":
            issues,
    }


# ============================================================
# LLM AVAILABILITY
# ============================================================

def llm_available() -> bool:

    """
    True only when the local OpenAI configuration looks
    usable.
    """

    status = (
        get_llm_configuration_status()
    )

    return bool(
        status[
            "available"
        ]
    )


# ============================================================
# OPENAI CLIENT
# ============================================================

def get_openai_client() -> OpenAI:

    """
    Build the OpenAI client.

    Raises a clear configuration error instead of allowing
    an obscure authentication/model error later.
    """

    status = (
        get_llm_configuration_status()
    )

    if (
        not status[
            "available"
        ]
    ):

        issues = (
            "; ".join(
                status[
                    "issues"
                ]
            )
        )

        raise RuntimeError(
            (
                "OpenAI is not configured correctly. "
                f"{issues}"
            )
        )

    api_key = (
        get_openai_api_key()
    )

    return OpenAI(
        api_key=
            api_key
    )