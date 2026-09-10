from __future__ import annotations

import json

from typing import Any

from fastapi.encoders import (
    jsonable_encoder,
)

from sqlalchemy import text

from ..database import engine


# ============================================================
# SERIALIZATION
# ============================================================

def serialize_payload(
    value: Any,
) -> str:

    return json.dumps(
        jsonable_encoder(
            value
        )
    )


def serialize_job(
    row,
) -> dict:

    return dict(
        row
    )


def serialize_event(
    row,
) -> dict:

    return dict(
        row
    )


# ============================================================
# CREATE EVENT
# ============================================================

def add_job_event(
    connection,
    *,
    job_id: int,
    event_type: str,
    stage: str,
    message: str,
    payload: Any = None,
) -> None:

    payload_json = (
        None
        if payload is None
        else
        serialize_payload(
            payload
        )
    )


    connection.execute(
        text(
            """
            INSERT INTO
                analytics.intelligence_job_events
            (
                job_id,
                event_type,
                stage,
                message,
                payload
            )
            VALUES
            (
                :job_id,
                :event_type,
                :stage,
                :message,
                CAST(
                    :payload_json
                    AS JSONB
                )
            );
            """
        ),
        {
            "job_id":
                job_id,

            "event_type":
                event_type,

            "stage":
                stage,

            "message":
                message,

            "payload_json":
                payload_json,
        },
    )


# ============================================================
# ACTIVE JOB LOOKUP
# ============================================================

def get_active_job(
    job_type: str,
) -> dict | None:

    with engine.connect() as connection:

        row = (
            connection.execute(
                text(
                    """
                    SELECT
                        *
                    FROM
                        analytics.intelligence_jobs

                    WHERE
                        job_type =
                            :job_type

                        AND
                        status IN
                        (
                            'QUEUED',
                            'RUNNING'
                        )

                    ORDER BY
                        created_at DESC

                    LIMIT 1;
                    """
                ),
                {
                    "job_type":
                        job_type,
                },
            )
            .mappings()
            .first()
        )


    if row is None:

        return None


    return serialize_job(
        row
    )


# ============================================================
# CREATE JOB
# ============================================================

def create_job(
    *,
    job_type: str,
    requested_by: str,
) -> dict:

    with engine.begin() as connection:

        row = (
            connection.execute(
                text(
                    """
                    INSERT INTO
                        analytics.intelligence_jobs
                    (
                        job_type,
                        status,
                        stage,
                        progress_pct,
                        requested_by,
                        message
                    )
                    VALUES
                    (
                        :job_type,
                        'QUEUED',
                        'QUEUED',
                        0,
                        :requested_by,
                        'Job queued.'
                    )
                    RETURNING
                        *;
                    """
                ),
                {
                    "job_type":
                        job_type,

                    "requested_by":
                        requested_by,
                },
            )
            .mappings()
            .one()
        )


        job = serialize_job(
            row
        )


        add_job_event(
            connection,
            job_id=
                job[
                    "job_id"
                ],
            event_type=
                "JOB_QUEUED",
            stage=
                "QUEUED",
            message=
                "Background intelligence job queued.",
        )


    return job


# ============================================================
# GET JOB
# ============================================================

def get_job(
    job_id: int,
) -> dict | None:

    with engine.connect() as connection:

        row = (
            connection.execute(
                text(
                    """
                    SELECT
                        *
                    FROM
                        analytics.intelligence_jobs
                    WHERE
                        job_id =
                            :job_id;
                    """
                ),
                {
                    "job_id":
                        job_id,
                },
            )
            .mappings()
            .first()
        )


    if row is None:

        return None


    return serialize_job(
        row
    )


# ============================================================
# LATEST JOB
# ============================================================

def get_latest_job(
    job_type: str | None = None,
) -> dict | None:

    with engine.connect() as connection:

        if job_type:

            row = (
                connection.execute(
                    text(
                        """
                        SELECT
                            *
                        FROM
                            analytics.intelligence_jobs
                        WHERE
                            job_type =
                                :job_type
                        ORDER BY
                            created_at DESC
                        LIMIT 1;
                        """
                    ),
                    {
                        "job_type":
                            job_type,
                    },
                )
                .mappings()
                .first()
            )

        else:

            row = (
                connection.execute(
                    text(
                        """
                        SELECT
                            *
                        FROM
                            analytics.intelligence_jobs
                        ORDER BY
                            created_at DESC
                        LIMIT 1;
                        """
                    )
                )
                .mappings()
                .first()
            )


    if row is None:

        return None


    return serialize_job(
        row
    )


# ============================================================
# LIST JOBS
# ============================================================

def list_jobs(
    limit: int = 20,
) -> list[dict]:

    safe_limit = max(
        1,
        min(
            limit,
            100,
        ),
    )


    with engine.connect() as connection:

        rows = (
            connection.execute(
                text(
                    """
                    SELECT
                        *
                    FROM
                        analytics.intelligence_jobs
                    ORDER BY
                        created_at DESC
                    LIMIT
                        :limit;
                    """
                ),
                {
                    "limit":
                        safe_limit,
                },
            )
            .mappings()
            .all()
        )


    return [
        serialize_job(
            row
        )
        for row
        in rows
    ]


# ============================================================
# JOB EVENTS
# ============================================================

def get_job_events(
    job_id: int,
) -> list[dict]:

    with engine.connect() as connection:

        rows = (
            connection.execute(
                text(
                    """
                    SELECT
                        *
                    FROM
                        analytics.intelligence_job_events
                    WHERE
                        job_id =
                            :job_id
                    ORDER BY
                        created_at ASC,
                        event_id ASC;
                    """
                ),
                {
                    "job_id":
                        job_id,
                },
            )
            .mappings()
            .all()
        )


    return [
        serialize_event(
            row
        )
        for row
        in rows
    ]


# ============================================================
# MARK RUNNING
# ============================================================

def mark_job_running(
    job_id: int,
    *,
    stage: str,
    progress_pct: int,
    message: str,
) -> None:

    with engine.begin() as connection:

        connection.execute(
            text(
                """
                UPDATE
                    analytics.intelligence_jobs

                SET
                    status =
                        'RUNNING',

                    stage =
                        :stage,

                    progress_pct =
                        :progress_pct,

                    message =
                        :message,

                    started_at =
                        COALESCE(
                            started_at,
                            NOW()
                        )

                WHERE
                    job_id =
                        :job_id;
                """
            ),
            {
                "job_id":
                    job_id,

                "stage":
                    stage,

                "progress_pct":
                    progress_pct,

                "message":
                    message,
            },
        )


        add_job_event(
            connection,
            job_id=
                job_id,
            event_type=
                "JOB_STAGE",
            stage=
                stage,
            message=
                message,
        )


# ============================================================
# UPDATE STAGE
# ============================================================

def update_job_stage(
    job_id: int,
    *,
    stage: str,
    progress_pct: int,
    message: str,
    payload: Any = None,
) -> None:

    with engine.begin() as connection:

        connection.execute(
            text(
                """
                UPDATE
                    analytics.intelligence_jobs

                SET
                    stage =
                        :stage,

                    progress_pct =
                        :progress_pct,

                    message =
                        :message

                WHERE
                    job_id =
                        :job_id;
                """
            ),
            {
                "job_id":
                    job_id,

                "stage":
                    stage,

                "progress_pct":
                    progress_pct,

                "message":
                    message,
            },
        )


        add_job_event(
            connection,
            job_id=
                job_id,
            event_type=
                "JOB_STAGE",
            stage=
                stage,
            message=
                message,
            payload=
                payload,
        )


# ============================================================
# COMPLETE
# ============================================================

def mark_job_completed(
    job_id: int,
    *,
    result: Any,
    message: str,
) -> None:

    result_json = serialize_payload(
        result
    )


    with engine.begin() as connection:

        connection.execute(
            text(
                """
                UPDATE
                    analytics.intelligence_jobs

                SET
                    status =
                        'COMPLETED',

                    stage =
                        'COMPLETED',

                    progress_pct =
                        100,

                    message =
                        :message,

                    result =
                        CAST(
                            :result_json
                            AS JSONB
                        ),

                    error_detail =
                        NULL,

                    completed_at =
                        NOW()

                WHERE
                    job_id =
                        :job_id;
                """
            ),
            {
                "job_id":
                    job_id,

                "message":
                    message,

                "result_json":
                    result_json,
            },
        )


        add_job_event(
            connection,
            job_id=
                job_id,
            event_type=
                "JOB_COMPLETED",
            stage=
                "COMPLETED",
            message=
                message,
            payload=
                result,
        )


# ============================================================
# FAIL
# ============================================================

def mark_job_failed(
    job_id: int,
    *,
    error_detail: str,
) -> None:

    with engine.begin() as connection:

        connection.execute(
            text(
                """
                UPDATE
                    analytics.intelligence_jobs

                SET
                    status =
                        'FAILED',

                    stage =
                        'FAILED',

                    message =
                        'Job failed.',

                    error_detail =
                        :error_detail,

                    completed_at =
                        NOW()

                WHERE
                    job_id =
                        :job_id;
                """
            ),
            {
                "job_id":
                    job_id,

                "error_detail":
                    error_detail,
            },
        )


        add_job_event(
            connection,
            job_id=
                job_id,
            event_type=
                "JOB_FAILED",
            stage=
                "FAILED",
            message=
                error_detail,
        )


# ============================================================
# DELETE JOB
# ============================================================

def delete_job(
    job_id: int,
) -> None:

    with engine.begin() as connection:

        connection.execute(
            text(
                """
                DELETE FROM
                    analytics.intelligence_jobs
                WHERE
                    job_id =
                        :job_id;
                """
            ),
            {
                "job_id":
                    job_id,
            },
        )