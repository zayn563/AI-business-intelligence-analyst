from __future__ import annotations

from copy import deepcopy

from uuid import uuid4

from fastapi import (
    APIRouter,
    HTTPException,
    Query,
)

from ..analyst.models import (
    AnalystAskRequest,
)

from ..analyst.orchestrator import (
    ask_analyst,
)

from ..analyst.recommendation_service import (
    build_recommendation_response,
    is_recommendation_question,
)

from ..analyst.recommendation_focus_guard import (
    apply_recommendation_focus_guard,
)


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/analyst",
    tags=[
        "Business Analyst"
    ],
)


# ============================================================
# FRIENDLY ERROR DETAIL
# ============================================================

def _error_detail(
    error: Exception,
) -> str:

    message = (
        str(error)
        .strip()
    )

    if not message:

        message = repr(
            error
        )

    return (
        f"{type(error).__name__}: "
        f"{message}"
    )


# ============================================================
# EXECUTION METADATA NORMALIZATION
#
# This keeps API metadata consistent even when an older
# orchestrator path omits execution_mode or incorrectly
# reports used_llm.
#
# We do NOT alter:
# - analytical evidence
# - intent
# - answer
# - tool routing
# - KPI calculations
# ============================================================

def normalize_execution_metadata(
    result: dict,
) -> dict:

    normalized = deepcopy(
        result
    )

    parser = (
        str(
            normalized.get(
                "parser"
            )
            or
            ""
        )
        .strip()
        .lower()
    )

    llm_usage = (
        normalized.get(
            "llm_usage"
        )
    )

    if not isinstance(
        llm_usage,
        dict,
    ):

        llm_usage = {}

    # --------------------------------------------------------
    # OLLAMA INTENT PARSER
    # --------------------------------------------------------

    if (
        parser
        ==
        "ollama_structured"
    ):

        normalized[
            "used_llm"
        ] = True

        llm_usage[
            "intent"
        ] = True

        llm_usage.setdefault(
            "response",
            False,
        )

        normalized[
            "execution_mode"
        ] = (
            "local_ai"
        )

    # --------------------------------------------------------
    # DETERMINISTIC ANALYST FAST PATH
    # --------------------------------------------------------

    elif (
        parser
        ==
        "deterministic_fast_path"
    ):

        normalized[
            "used_llm"
        ] = False

        llm_usage[
            "intent"
        ] = False

        llm_usage.setdefault(
            "response",
            False,
        )

        normalized[
            "execution_mode"
        ] = (
            "fast_path"
        )

    # --------------------------------------------------------
    # DETERMINISTIC RECOMMENDATION ENGINE
    # --------------------------------------------------------

    elif (
        parser
        ==
        "deterministic_recommendation"
    ):

        normalized[
            "used_llm"
        ] = False

        llm_usage[
            "intent"
        ] = False

        llm_usage[
            "response"
        ] = False

        normalized[
            "execution_mode"
        ] = (
            "fast_path"
        )

    # --------------------------------------------------------
    # GUARDRAIL
    # --------------------------------------------------------

    elif (
        parser
        ==
        "intent_guardrail"
    ):

        normalized[
            "used_llm"
        ] = False

        llm_usage.setdefault(
            "intent",
            False,
        )

        llm_usage.setdefault(
            "response",
            False,
        )

        normalized[
            "execution_mode"
        ] = (
            "guardrail"
        )

    else:

        normalized.setdefault(
            "used_llm",
            False,
        )

        normalized.setdefault(
            "execution_mode",
            "unknown",
        )

        llm_usage.setdefault(
            "intent",
            False,
        )

        llm_usage.setdefault(
            "response",
            False,
        )

    normalized[
        "llm_usage"
    ] = llm_usage

    return normalized


# ============================================================
# CONTROLLED SEMANTIC FAILURE
# ============================================================

def _semantic_guardrail_response(
    question: str,
) -> dict:

    return {
        "status":
            "unsupported",

        "question":
            question,

        "answer":
            (
                "I understood this as a business-analysis "
                "request, but I could not resolve a valid "
                "business entity for the requested analysis. "
                "Try naming a specific region, product, store "
                "or KPI, or ask which areas require attention."
            ),

        "intent": {
            "analysis_type":
                "unsupported",

            "metric":
                None,

            "dimension":
                None,

            "dimension_value":
                None,

            "current_start":
                None,

            "current_end":
                None,

            "comparison_start":
                None,

            "comparison_end":
                None,

            "target_month":
                None,

            "promotion_start":
                None,

            "promotion_end":
                None,

            "confidence":
                0.0,
        },

        "parser":
            "intent_guardrail",

        "tool_used":
            "none",

        "used_llm":
            False,

        "llm_usage": {
            "intent":
                False,

            "response":
                False,
        },

        "execution_mode":
            "guardrail",

        "response_time_ms":
            0.0,

        "evidence":
            {},

        "warnings": [
            (
                "A parsed business entity could not be "
                "validated against the analytical data."
            )
        ],

        "analysis_id":
            str(
                uuid4()
            ),
    }


# ============================================================
# ASK ANALYST
# ============================================================

@router.post(
    "/ask"
)
def ask_analyst_endpoint(
    request: AnalystAskRequest,
):

    question = (
        request.question
        .strip()
    )

    if not question:

        raise HTTPException(
            status_code=400,
            detail=(
                "Question cannot be empty."
            ),
        )

    # --------------------------------------------------------
    # MANAGEMENT RECOMMENDATION FAST PATH
    # --------------------------------------------------------

    if (
        is_recommendation_question(
            question
        )
    ):

        try:

            result = (
                build_recommendation_response(
                    question
                )
            )

            result = (
                apply_recommendation_focus_guard(
                    result
                )
            )

            return (
                normalize_execution_metadata(
                    result
                )
            )

        except Exception as error:

            raise HTTPException(
                status_code=500,
                detail=_error_detail(
                    error
                ),
            ) from error

    # --------------------------------------------------------
    # EXISTING ANALYST ORCHESTRATOR
    # --------------------------------------------------------

    try:

        result = (
            ask_analyst(
                question
            )
        )

        if not isinstance(
            result,
            dict,
        ):

            raise TypeError(
                (
                    "Analyst orchestrator returned an "
                    "unexpected response type."
                )
            )

        return (
            normalize_execution_metadata(
                result
            )
        )

    # --------------------------------------------------------
    # INTENT / ENTITY FAILURE
    # --------------------------------------------------------

    except (
        ValueError,
        KeyError,
    ):

        return (
            normalize_execution_metadata(
                _semantic_guardrail_response(
                    question
                )
            )
        )

    # --------------------------------------------------------
    # TRUE SYSTEM FAILURE
    # --------------------------------------------------------

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=_error_detail(
                error
            ),
        ) from error


# ============================================================
# RECOMMENDATIONS
# ============================================================

@router.get(
    "/recommendations"
)
def analyst_recommendations(
    region: str | None = Query(
        default=None
    ),
    limit: int = Query(
        default=4,
        ge=1,
        le=10,
    ),
):

    if region:

        question = (
            "What actions should we take "
            f"to improve performance in {region}?"
        )

    else:

        question = (
            "How can we improve performance "
            "in regions which require attention?"
        )

    try:

        result = (
            build_recommendation_response(
                question=question,
                limit=limit,
            )
        )

        result = (
            apply_recommendation_focus_guard(
                result
            )
        )

        return (
            normalize_execution_metadata(
                result
            )
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=_error_detail(
                error
            ),
        ) from error


# ============================================================
# CAPABILITIES
# ============================================================

@router.get(
    "/capabilities"
)
def analyst_capabilities():

    return {
        "application":
            "AI Business Intelligence Analyst",

        "local_first":
            True,

        "supported_analysis": [
            "latest_changes",
            "diagnostic",
            "targets",
            "promotions",
            "recommendations",
        ],

        "decision_support": {
            "recommendation_engine":
                True,

            "verified_evidence_only":
                True,

            "persistent_priorities":
                True,

            "risk_opportunity_separation":
                True,

            "action_ready":
                True,
        },

        "guardrails": {
            "llm_calculates_kpis":
                False,

            "unrestricted_llm_sql":
                False,

            "invalid_entity_returns_http_500":
                False,

            "execution_metadata_normalized":
                True,
        },

        "example_questions": [
            (
                "Why did North sales decline "
                "in June 2026?"
            ),
            (
                "What drove South margin "
                "deterioration in July 2026?"
            ),
            (
                "How did East perform against "
                "target in July 2026?"
            ),
            (
                "Did the April 2026 promotion "
                "work?"
            ),
            (
                "How can we improve sales in "
                "regions which require attention?"
            ),
            (
                "What should we do about South "
                "margin deterioration?"
            ),
            (
                "What should we do to scale the "
                "North growth opportunity?"
            ),
        ],
    }