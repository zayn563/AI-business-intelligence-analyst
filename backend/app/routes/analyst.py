from time import perf_counter

from fastapi import (
    APIRouter,
)

from ..config import settings

from ..analyst.models import (
    AnalystAskRequest,
    AnalystAskResponse,
)

from ..analyst.orchestrator import (
    ask_analyst,
)


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix=
        "/analyst",

    tags=[
        "Analyst",
    ],
)


# ============================================================
# CAPABILITIES
# ============================================================

@router.get(
    "/capabilities"
)
def analyst_capabilities():

    return {
        "status":
            "ready",

        "analyst_mode":
            "hybrid_local",

        "llm_provider":
            settings.llm_provider,

        "llm_model":
            settings.ollama_model,

        "fast_path_enabled":
            True,

        "llm_response_rewriting":
            settings.analyst_use_llm_response,

        "supported_analysis": [
            "business change detection",
            "performance driver diagnostics",
            "target achievement",
            "promotion effectiveness",
        ],

        "example_questions": [
            (
                "Why did North sales decline "
                "in June 2026?"
            ),

            (
                "How did East perform against "
                "target in July 2026?"
            ),

            (
                "Did the April 2026 "
                "promotion work?"
            ),

            (
                "What drove South margin "
                "deterioration in July 2026?"
            ),

            (
                "What are the most important "
                "business issues I should focus on?"
            ),
        ],
    }


# ============================================================
# ASK ANALYST
# ============================================================

@router.post(
    "/ask",
    response_model=
        AnalystAskResponse,
)
def ask_analyst_endpoint(
    request: AnalystAskRequest,
):

    started = (
        perf_counter()
    )


    # --------------------------------------------------------
    # EXISTING ORCHESTRATOR
    # --------------------------------------------------------

    result = (
        ask_analyst(
            request.question
        )
    )


    # --------------------------------------------------------
    # SUPPORT DICT OR PYDANTIC RESPONSE
    # --------------------------------------------------------

    if hasattr(
        result,
        "model_dump",
    ):

        payload = (
            result.model_dump()
        )

    else:

        payload = dict(
            result
        )


    # --------------------------------------------------------
    # LLM USAGE
    # --------------------------------------------------------

    parser = (
        payload.get(
            "parser",
            "unknown",
        )
    )

    response_llm_used = bool(
        payload.get(
            "used_llm",
            False,
        )
    )

    intent_llm_used = (
        parser
        ==
        "ollama_structured"
    )

    payload[
        "llm_usage"
    ] = {
        "intent":
            intent_llm_used,

        "response":
            response_llm_used,
    }

    payload[
        "used_llm"
    ] = (
        intent_llm_used
        or
        response_llm_used
    )


    # --------------------------------------------------------
    # EXECUTION MODE
    # --------------------------------------------------------

    if (
        parser
        ==
        "deterministic_fast_path"
    ):

        execution_mode = (
            "fast_path"
        )

    elif (
        parser
        ==
        "ollama_structured"
    ):

        execution_mode = (
            "local_ai"
        )

    else:

        execution_mode = (
            "fallback"
        )

    payload[
        "execution_mode"
    ] = (
        execution_mode
    )


    # --------------------------------------------------------
    # RESPONSE TIME
    # --------------------------------------------------------

    elapsed_ms = (
        (
            perf_counter()
            -
            started
        )
        *
        1000
    )

    payload[
        "response_time_ms"
    ] = round(
        elapsed_ms,
        2,
    )


    # --------------------------------------------------------
    # VALIDATED RESPONSE
    # --------------------------------------------------------

    return (
        AnalystAskResponse
        .model_validate(
            payload
        )
    )