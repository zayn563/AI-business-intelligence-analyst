from fastapi import (
    APIRouter,
    HTTPException,
)

from ..analyst.models import (
    AnalystAskRequest,
    AnalystAskResponse,
)

from ..analyst.orchestrator import (
    ask_analyst,
)


router = APIRouter(
    prefix="/analyst",
    tags=[
        "AI Business Analyst"
    ],
)


# ============================================================
# ERROR DETAIL
# ============================================================

def error_detail(
    error: Exception,
) -> str:

    message = (
        str(error)
        .strip()
    )

    if not message:

        message = (
            repr(error)
        )

    return (
        f"{type(error).__name__}: "
        f"{message}"
    )


# ============================================================
# CAPABILITIES
# ============================================================

@router.get("/capabilities")
def analyst_capabilities():

    return {
        "status":
            "ready",

        "supported_questions": [
            "What changed in the business?",
            "Why did North sales decline in June?",
            "Which regions missed target in July?",
            "Did the April promotion work?",
            "What drove South margin deterioration?",
        ],

        "supported_analysis": [
            "business_change_detection",
            "driver_diagnostics",
            "target_achievement",
            "promotion_effectiveness",
        ],

        "design_principle":
            (
                "The AI interprets questions and explains "
                "verified results. KPI calculations remain "
                "deterministic."
            ),
    }


# ============================================================
# ASK ANALYST
# ============================================================

@router.post(
    "/ask",
    response_model=
        AnalystAskResponse,
)
def ask_business_analyst(
    request: AnalystAskRequest,
):

    try:

        return (
            ask_analyst(
                request.question
            )
        )

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=error_detail(
                error
            ),
        ) from error

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=error_detail(
                error
            ),
        ) from error