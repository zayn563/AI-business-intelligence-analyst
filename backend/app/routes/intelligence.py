
from datetime import date

from ..intelligence.target_analysis import (
    analyze_targets,
)

from ..intelligence.promotion_analysis import (
    analyze_promotions,
)
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

    # ============================================================
# TARGET ACHIEVEMENT
# ============================================================

@router.get("/targets")
def target_achievement(
    month_start: date | None = None,
):

    try:

        return analyze_targets(
            month_start=
                month_start
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=error_detail(
                error
            ),
        ) from error


# ============================================================
# PROMOTION EFFECTIVENESS
# ============================================================

@router.get("/promotions")
def promotion_effectiveness(
    start_date: date,
    end_date: date,
):

    try:

        if (
            start_date
            >
            end_date
        ):

            raise ValueError(
                "start_date cannot be "
                "after end_date."
            )

        return analyze_promotions(
            start_date=
                start_date,

            end_date=
                end_date,
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=error_detail(
                error
            ),
        ) from error