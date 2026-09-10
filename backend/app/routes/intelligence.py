from datetime import date

from fastapi import (
    APIRouter,
    HTTPException,
)

from ..dashboard.summary_service import (
    get_dashboard_summary,
)

from ..decision.action_models import (
    ActionCreateRequest,
    ActionUpdateRequest,
)

from ..decision.action_service import (
    create_insight_action,
    delete_action,
    list_insight_actions,
    update_action,
)

from ..decision.insight_service import (
    get_active_insights,
    get_all_insights,
    get_insight,
)

from ..decision.investigation_service import (
    investigate_insight,
)

from ..decision.models import (
    ScenarioRequest,
)

from ..decision.run_service import (
    run_decision_intelligence,
)

from ..decision.scenario_service import (
    run_scenario,
)

from ..intelligence.intelligence_service import (
    run_business_intelligence,
)

from ..intelligence.models import (
    IntelligenceRunRequest,
)

from ..intelligence.promotion_analysis import (
    analyze_promotions,
)

from ..intelligence.target_analysis import (
    analyze_targets,
)

from ..jobs.job_runner import (
    submit_job,
)

from ..jobs.job_store import (
    create_job,
    get_active_job,
    get_job,
    get_job_events,
    get_latest_job,
    list_jobs,
)

from ..jobs.models import (
    IntelligenceJobCreateRequest,
)


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/intelligence",
    tags=[
        "Business Intelligence",
    ],
)


# ============================================================
# ERROR DETAIL
# ============================================================

def error_detail(
    error: Exception,
) -> str:

    message = (
        str(
            error
        )
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
# BACKGROUND JOB — CREATE
# ============================================================

@router.post(
    "/jobs"
)
def start_intelligence_job(
    request:
        IntelligenceJobCreateRequest,
):

    try:

        active_job = (
            get_active_job(
                request.job_type
            )
        )


        if (
            active_job
            is not None
        ):

            return {
                "created":
                    False,

                "reused":
                    True,

                "job":
                    active_job,
            }


        job = create_job(
            job_type=
                request.job_type,
            requested_by=
                request.requested_by,
        )


        submit_job(
            job[
                "job_id"
            ],
            job[
                "job_type"
            ],
        )


        return {
            "created":
                True,

            "reused":
                False,

            "job":
                job,
        }


    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=
                error_detail(
                    error
                ),
        ) from error


# ============================================================
# BACKGROUND JOB — LATEST
# ============================================================

@router.get(
    "/jobs/latest"
)
def latest_intelligence_job(
    job_type: str | None = None,
):

    try:

        job = get_latest_job(
            job_type
        )


        if job is None:

            raise HTTPException(
                status_code=404,
                detail=
                    "No intelligence jobs found.",
            )


        return job


    except HTTPException:

        raise


    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=
                error_detail(
                    error
                ),
        ) from error


# ============================================================
# BACKGROUND JOB — LIST
# ============================================================

@router.get(
    "/jobs"
)
def intelligence_jobs(
    limit: int = 20,
):

    try:

        jobs = list_jobs(
            limit
        )


        return {
            "count":
                len(
                    jobs
                ),

            "results":
                jobs,
        }


    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=
                error_detail(
                    error
                ),
        ) from error


# ============================================================
# BACKGROUND JOB — EVENTS
# ============================================================

@router.get(
    "/jobs/{job_id}/events"
)
def intelligence_job_events(
    job_id: int,
):

    try:

        job = get_job(
            job_id
        )


        if job is None:

            raise HTTPException(
                status_code=404,
                detail=
                    "Intelligence job not found.",
            )


        events = (
            get_job_events(
                job_id
            )
        )


        return {
            "job_id":
                job_id,

            "count":
                len(
                    events
                ),

            "results":
                events,
        }


    except HTTPException:

        raise


    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=
                error_detail(
                    error
                ),
        ) from error


# ============================================================
# BACKGROUND JOB — SINGLE JOB
# ============================================================

@router.get(
    "/jobs/{job_id}"
)
def intelligence_job(
    job_id: int,
):

    try:

        job = get_job(
            job_id
        )


        if job is None:

            raise HTTPException(
                status_code=404,
                detail=
                    "Intelligence job not found.",
            )


        return job


    except HTTPException:

        raise


    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=
                error_detail(
                    error
                ),
        ) from error


# ============================================================
# DECISION INTELLIGENCE RUN
# ============================================================

@router.post(
    "/run"
)
def run_intelligence_cycle():

    try:

        return (
            run_decision_intelligence()
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=
                error_detail(
                    error
                ),
        ) from error


# ============================================================
# READ-ONLY DASHBOARD
# ============================================================

@router.get(
    "/dashboard-summary"
)
def dashboard_summary():

    try:

        return (
            get_dashboard_summary()
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=
                error_detail(
                    error
                ),
        ) from error


# ============================================================
# PERSISTED PRIORITIES
# ============================================================

@router.get(
    "/priorities"
)
def priorities(
    include_resolved: bool = False,
):

    try:

        insights = (
            get_all_insights()
            if
            include_resolved
            else
            get_active_insights()
        )


        return {
            "count":
                len(
                    insights
                ),

            "results":
                insights,
        }


    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=
                error_detail(
                    error
                ),
        ) from error


# ============================================================
# SINGLE INSIGHT
# ============================================================

@router.get(
    "/insights/{insight_id}"
)
def insight(
    insight_id: int,
):

    try:

        return get_insight(
            insight_id
        )

    except ValueError as error:

        raise HTTPException(
            status_code=404,
            detail=
                str(
                    error
                ),
        ) from error

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=
                error_detail(
                    error
                ),
        ) from error


# ============================================================
# INVESTIGATION
# ============================================================

@router.get(
    "/insights/{insight_id}/investigation"
)
def investigation(
    insight_id: int,
):

    try:

        return investigate_insight(
            insight_id
        )

    except ValueError as error:

        raise HTTPException(
            status_code=404,
            detail=
                str(
                    error
                ),
        ) from error

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=
                error_detail(
                    error
                ),
        ) from error


# ============================================================
# ACTIONS — LIST
# ============================================================

@router.get(
    "/insights/{insight_id}/actions"
)
def insight_actions(
    insight_id: int,
):

    try:

        actions = (
            list_insight_actions(
                insight_id
            )
        )


        return {
            "count":
                len(
                    actions
                ),

            "results":
                actions,
        }

    except ValueError as error:

        raise HTTPException(
            status_code=404,
            detail=
                str(
                    error
                ),
        ) from error

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=
                error_detail(
                    error
                ),
        ) from error


# ============================================================
# ACTIONS — CREATE
# ============================================================

@router.post(
    "/insights/{insight_id}/actions"
)
def create_action(
    insight_id: int,
    request: ActionCreateRequest,
):

    try:

        return create_insight_action(
            insight_id,
            request,
        )

    except ValueError as error:

        raise HTTPException(
            status_code=404,
            detail=
                str(
                    error
                ),
        ) from error

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=
                error_detail(
                    error
                ),
        ) from error


# ============================================================
# ACTIONS — UPDATE
# ============================================================

@router.patch(
    "/actions/{action_id}"
)
def edit_action(
    action_id: int,
    request: ActionUpdateRequest,
):

    try:

        return update_action(
            action_id,
            request,
        )

    except ValueError as error:

        raise HTTPException(
            status_code=404,
            detail=
                str(
                    error
                ),
        ) from error

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=
                error_detail(
                    error
                ),
        ) from error


# ============================================================
# ACTIONS — DELETE
# ============================================================

@router.delete(
    "/actions/{action_id}"
)
def remove_action(
    action_id: int,
):

    try:

        return delete_action(
            action_id
        )

    except ValueError as error:

        raise HTTPException(
            status_code=404,
            detail=
                str(
                    error
                ),
        ) from error

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=
                error_detail(
                    error
                ),
        ) from error


# ============================================================
# SCENARIO
# ============================================================

@router.post(
    "/scenario"
)
def scenario(
    request: ScenarioRequest,
):

    try:

        return run_scenario(
            request
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=
                error_detail(
                    error
                ),
        ) from error


# ============================================================
# LATEST BUSINESS INTELLIGENCE
# ============================================================

@router.get(
    "/latest"
)
def latest_business_intelligence():

    try:

        return run_business_intelligence(
            IntelligenceRunRequest()
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=
                error_detail(
                    error
                ),
        ) from error


# ============================================================
# EXPLICIT CHANGE DETECTION
# ============================================================

@router.post(
    "/detect"
)
def detect_business_changes(
    request: IntelligenceRunRequest,
):

    try:

        return run_business_intelligence(
            request
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=
                error_detail(
                    error
                ),
        ) from error


# ============================================================
# TARGETS
# ============================================================

@router.get(
    "/targets"
)
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
            detail=
                error_detail(
                    error
                ),
        ) from error


# ============================================================
# PROMOTIONS
# ============================================================

@router.get(
    "/promotions"
)
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
                (
                    "start_date cannot be "
                    "after end_date."
                )
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
            detail=
                error_detail(
                    error
                ),
        ) from error