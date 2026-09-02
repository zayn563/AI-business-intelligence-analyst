from __future__ import annotations

import os

from concurrent.futures import (
    ThreadPoolExecutor,
)

import httpx

from fastapi.encoders import (
    jsonable_encoder,
)

from ..decision.run_service import (
    run_decision_intelligence,
)

from .job_store import (
    mark_job_completed,
    mark_job_failed,
    mark_job_running,
    update_job_stage,
)


# ============================================================
# CONFIGURATION
# ============================================================

BACKEND_SELF_URL = (
    os.getenv(
        "AIBI_BACKEND_SELF_URL",
        "http://127.0.0.1:8000",
    )
    .rstrip(
        "/"
    )
)


REFRESH_TIMEOUT_SECONDS = float(
    os.getenv(
        "AIBI_REFRESH_TIMEOUT_SECONDS",
        "1800",
    )
)


# ============================================================
# EXECUTOR
# ============================================================

executor = ThreadPoolExecutor(
    max_workers=2,
    thread_name_prefix=
        "aibi-background-job",
)


# ============================================================
# REFRESH SOURCE
# ============================================================

def run_source_refresh() -> dict:

    with httpx.Client(
        timeout=
            REFRESH_TIMEOUT_SECONDS
    ) as client:

        response = client.post(
            (
                f"{BACKEND_SELF_URL}"
                "/pipeline/refresh"
            )
        )


        response.raise_for_status()


        return response.json()


# ============================================================
# ANALYZE CURRENT DATA
# ============================================================

def run_current_intelligence():

    result = (
        run_decision_intelligence()
    )


    return jsonable_encoder(
        result
    )


# ============================================================
# EXECUTE JOB
# ============================================================

def execute_job(
    job_id: int,
    job_type: str,
) -> None:

    try:

        # ----------------------------------------------------
        # ANALYZE ONLY
        # ----------------------------------------------------

        if (
            job_type
            ==
            "ANALYZE_ONLY"
        ):

            mark_job_running(
                job_id,
                stage=
                    "ANALYZING",
                progress_pct=
                    30,
                message=
                    (
                        "Running decision intelligence "
                        "against current PostgreSQL data."
                    ),
            )


            intelligence_result = (
                run_current_intelligence()
            )


            mark_job_completed(
                job_id,
                result={
                    "job_type":
                        job_type,

                    "intelligence":
                        intelligence_result,
                },
                message=
                    (
                        "Decision intelligence "
                        "completed successfully."
                    ),
            )


            return


        # ----------------------------------------------------
        # FULL REFRESH + ANALYZE
        # ----------------------------------------------------

        if (
            job_type
            ==
            "REFRESH_AND_ANALYZE"
        ):

            mark_job_running(
                job_id,
                stage=
                    "REFRESHING",
                progress_pct=
                    10,
                message=
                    (
                        "Synchronizing the connected "
                        "business data source."
                    ),
            )


            refresh_result = (
                run_source_refresh()
            )


            update_job_stage(
                job_id,
                stage=
                    "ANALYZING",
                progress_pct=
                    70,
                message=
                    (
                        "Source refresh completed. "
                        "Running decision intelligence."
                    ),
                payload=
                    refresh_result,
            )


            intelligence_result = (
                run_current_intelligence()
            )


            mark_job_completed(
                job_id,
                result={
                    "job_type":
                        job_type,

                    "refresh":
                        refresh_result,

                    "intelligence":
                        intelligence_result,
                },
                message=
                    (
                        "Data synchronization and "
                        "decision intelligence completed."
                    ),
            )


            return


        raise ValueError(
            (
                "Unsupported intelligence job type: "
                f"{job_type}"
            )
        )


    except Exception as error:

        mark_job_failed(
            job_id,
            error_detail=
                (
                    f"{type(error).__name__}: "
                    f"{str(error)}"
                ),
        )


# ============================================================
# SUBMIT
# ============================================================

def submit_job(
    job_id: int,
    job_type: str,
) -> None:

    executor.submit(
        execute_job,
        job_id,
        job_type,
    )