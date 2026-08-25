import re
from time import monotonic

from ollama import Client

from ..config import settings


# ============================================================
# STATUS CACHE
# ============================================================

_LLM_STATUS_CACHE = {
    "value":
        None,

    "expires_at":
        0.0,
}


LLM_STATUS_CACHE_SECONDS = 30.0


# ============================================================
# CONFIGURATION
# ============================================================

def get_llm_provider() -> str:

    return (
        settings
        .llm_provider
        .strip()
        .lower()
    )


def get_ollama_base_url() -> str:

    return (
        settings
        .ollama_base_url
        .strip()
        .rstrip("/")
    )


def get_ollama_model() -> str:

    return (
        settings
        .ollama_model
        .strip()
    )


# ============================================================
# CLIENT
# ============================================================

def get_llm_client() -> Client:

    return Client(
        host=
            get_ollama_base_url(),

        timeout=
            180.0,
    )


# ============================================================
# LOCAL MODEL LISTING
# ============================================================

def get_local_model_names() -> list[str]:

    client = (
        get_llm_client()
    )

    response = (
        client.list()
    )

    model_names = []

    for model_info in (
        response.models
    ):

        model_name = (
            getattr(
                model_info,
                "model",
                None,
            )
        )

        if model_name:

            model_names.append(
                str(
                    model_name
                )
            )

    return model_names


# ============================================================
# CONFIGURATION STATUS
# ============================================================

def get_llm_configuration_status(
    force_refresh: bool = False,
) -> dict:

    now = (
        monotonic()
    )

    cached_value = (
        _LLM_STATUS_CACHE[
            "value"
        ]
    )

    cached_until = (
        _LLM_STATUS_CACHE[
            "expires_at"
        ]
    )

    if (
        not force_refresh
        and
        cached_value is not None
        and
        now
        <
        cached_until
    ):

        return dict(
            cached_value
        )


    provider = (
        get_llm_provider()
    )

    base_url = (
        get_ollama_base_url()
    )

    model = (
        get_ollama_model()
    )

    issues = []

    available_models = []


    # --------------------------------------------------------
    # PROVIDER
    # --------------------------------------------------------

    if (
        provider
        !=
        "ollama"
    ):

        issues.append(
            (
                "Unsupported LLM provider. "
                "This project currently uses Ollama."
            )
        )


    # --------------------------------------------------------
    # LOCAL SERVER
    # --------------------------------------------------------

    if not issues:

        try:

            available_models = (
                get_local_model_names()
            )

        except Exception as error:

            issues.append(
                (
                    "Could not connect to the local "
                    "Ollama service. "
                    f"{type(error).__name__}: "
                    f"{str(error)}"
                )
            )


    # --------------------------------------------------------
    # MODEL
    # --------------------------------------------------------

    if (
        not issues
        and
        model
        not in
        available_models
    ):

        issues.append(
            (
                f"Configured model '{model}' "
                "is not installed locally."
            )
        )


    status = {
        "available":
            len(
                issues
            )
            ==
            0,

        "provider":
            provider,

        "base_url":
            base_url,

        "model":
            model,

        "available_models":
            available_models,

        "issues":
            issues,
    }


    # --------------------------------------------------------
    # CACHE RESULT
    # --------------------------------------------------------

    _LLM_STATUS_CACHE[
        "value"
    ] = dict(
        status
    )

    _LLM_STATUS_CACHE[
        "expires_at"
    ] = (
        now
        +
        LLM_STATUS_CACHE_SECONDS
    )

    return status


# ============================================================
# AVAILABILITY
# ============================================================

def llm_available() -> bool:

    return bool(
        get_llm_configuration_status()
        [
            "available"
        ]
    )


# ============================================================
# THINKING CLEANUP
# ============================================================

def clean_llm_text(
    text: str | None,
) -> str:

    """
    Remove reasoning text that some local thinking models
    may accidentally expose inside message.content.
    """

    if not text:

        return ""

    cleaned = (
        str(
            text
        )
        .strip()
    )


    # --------------------------------------------------------
    # STANDARD THINK BLOCK
    # --------------------------------------------------------

    cleaned = re.sub(
        r"<think>.*?</think>",
        "",
        cleaned,
        flags=
            re.IGNORECASE
            |
            re.DOTALL,
    ).strip()


    # --------------------------------------------------------
    # QWEN CAN OCCASIONALLY RETURN ONLY THE CLOSING MARKER
    # --------------------------------------------------------

    lower_cleaned = (
        cleaned.lower()
    )

    if (
        "</think>"
        in
        lower_cleaned
    ):

        marker_index = (
            lower_cleaned
            .rfind(
                "</think>"
            )
        )

        cleaned = (
            cleaned[
                marker_index
                +
                len(
                    "</think>"
                ):
            ]
            .strip()
        )

    return cleaned


# ============================================================
# JSON EXTRACTION
# ============================================================

def extract_json_text(
    text: str | None,
) -> str:

    cleaned = (
        clean_llm_text(
            text
        )
    )

    if not cleaned:

        raise ValueError(
            "The local LLM returned an empty response."
        )

    first_brace = (
        cleaned.find(
            "{"
        )
    )

    last_brace = (
        cleaned.rfind(
            "}"
        )
    )

    if (
        first_brace
        ==
        -1
        or
        last_brace
        ==
        -1
        or
        last_brace
        <=
        first_brace
    ):

        raise ValueError(
            (
                "The local LLM response did not "
                "contain a JSON object."
            )
        )

    return (
        cleaned[
            first_brace:
            last_brace + 1
        ]
    )