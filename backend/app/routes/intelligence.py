from fastapi import (
    APIRouter,
    HTTPException,
)

from ..intelligence.intelligence_service import (
    run_business_intelligence,
)

from ..intelligence.models import (
    IntelligenceRunRequest,
)


router = APIRouter(
    prefix="/intelligence",
    tags=[
        "Business Intelligence"
    ],
)


def error_detail(
    error: Exception,
) -> str:

    message = str(
        error
    ).strip()

    if not message:

        message = repr(
            error
        )

    return (
        f"{type(error).__name__}: "
        f"{message}"
    )


# ============================================================
# AUTOMATIC LATEST PERIOD
# ============================================================

@router.get("/latest")
def latest_business_intelligence():

    try:

        return (
            run_business_intelligence(
                IntelligenceRunRequest()
            )
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=error_detail(
                error
            ),
        ) from error


# ============================================================
# EXPLICIT PERIOD COMPARISON
# ============================================================

@router.post("/detect")
def detect_business_changes(
    request: IntelligenceRunRequest,
):

    try:

        return (
            run_business_intelligence(
                request
            )
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=error_detail(
                error
            ),
        ) from error