from __future__ import annotations

import json

from datetime import date

from sqlalchemy import text

from ..database import engine


# ============================================================
# SEVERITY RANK
# ============================================================

SEVERITY_RANK = {
    "low":
        1,

    "medium":
        2,

    "high":
        3,
}


# ============================================================
# ROW SERIALIZATION
# ============================================================

def row_to_dict(
    row,
) -> dict:

    result = dict(
        row
    )

    payload = (
        result.get(
            "payload"
        )
    )

    if isinstance(
        payload,
        str,
    ):

        payload = json.loads(
            payload
        )

    payload = (
        payload
        or
        {}
    )

    return {
        **payload,

        "insight_id":
            result.get(
                "insight_id"
            ),

        "fingerprint":
            result.get(
                "fingerprint"
            ),

        "lifecycle_status":
            result.get(
                "lifecycle_status"
            ),

        "period_start":
            result.get(
                "period_start"
            ),

        "period_end":
            result.get(
                "period_end"
            ),

        "comparison_start":
            result.get(
                "comparison_start"
            ),

        "comparison_end":
            result.get(
                "comparison_end"
            ),

        "first_detected_at":
            result.get(
                "first_detected_at"
            ),

        "last_detected_at":
            result.get(
                "last_detected_at"
            ),

        "resolved_at":
            result.get(
                "resolved_at"
            ),

        "occurrence_count":
            result.get(
                "occurrence_count"
            ),
    }


# ============================================================
# SAME ANALYTICAL CYCLE
# ============================================================

def is_same_cycle(
    existing: dict,
    period_start: date,
    period_end: date,
    comparison_start: date,
    comparison_end: date,
) -> bool:

    return (
        existing.get(
            "period_start"
        )
        ==
        period_start

        and
        existing.get(
            "period_end"
        )
        ==
        period_end

        and
        existing.get(
            "comparison_start"
        )
        ==
        comparison_start

        and
        existing.get(
            "comparison_end"
        )
        ==
        comparison_end
    )


# ============================================================
# ESCALATION CHECK
# ============================================================

def has_escalated(
    existing: dict,
    priority: dict,
) -> bool:

    old_severity = (
        SEVERITY_RANK.get(
            str(
                existing.get(
                    "severity"
                )
                or
                "low"
            )
            .lower(),
            0,
        )
    )

    new_severity = (
        SEVERITY_RANK.get(
            str(
                priority.get(
                    "severity"
                )
                or
                "low"
            )
            .lower(),
            0,
        )
    )

    old_score = float(
        existing.get(
            "priority_score"
        )
        or
        0.0
    )

    new_score = float(
        priority.get(
            "priority_score"
        )
        or
        0.0
    )

    return (
        new_severity
        >
        old_severity

        or
        new_score
        >=
        old_score
        +
        15.0
    )


# ============================================================
# NEXT LIFECYCLE STATUS
# ============================================================

def next_status(
    existing: dict,
    priority: dict,
    same_cycle: bool,
) -> str:

    existing_status = str(
        existing.get(
            "lifecycle_status"
        )
        or
        "NEW"
    ).upper()

    # --------------------------------------------------------
    # A previously resolved issue appearing again is a new
    # business issue.
    # --------------------------------------------------------

    if existing_status == "RESOLVED":

        return "NEW"

    # --------------------------------------------------------
    # If evidence materially worsened, escalation is allowed
    # even within the same analytical period.
    # --------------------------------------------------------

    if has_escalated(
        existing,
        priority,
    ):

        return "ESCALATED"

    # --------------------------------------------------------
    # Re-running exactly the same analytical period should not
    # turn NEW into ONGOING merely because a browser refreshed
    # or automation retried the request.
    # --------------------------------------------------------

    if same_cycle:

        return existing_status

    # --------------------------------------------------------
    # The issue survived into a new analytical cycle.
    # --------------------------------------------------------

    return "ONGOING"


# ============================================================
# SYNC BUSINESS INSIGHTS
# ============================================================

def sync_business_insights(
    priorities: dict,
    period_start: date,
    period_end: date,
    comparison_start: date,
    comparison_end: date,
) -> dict[str, dict]:

    priority_items = (
        list(
            priorities.get(
                "risks",
                [],
            )
        )
        +
        list(
            priorities.get(
                "opportunities",
                [],
            )
        )
    )

    seen_fingerprints: set[str] = (
        set()
    )

    saved: dict[
        str,
        dict,
    ] = {}

    with engine.begin() as connection:

        # ----------------------------------------------------
        # UPSERT CURRENT INSIGHTS
        # ----------------------------------------------------

        for priority in (
            priority_items
        ):

            fingerprint = str(
                priority[
                    "fingerprint"
                ]
            )

            seen_fingerprints.add(
                fingerprint
            )

            existing = (
                connection.execute(
                    text(
                        """
                        SELECT
                            *
                        FROM
                            analytics.business_insights
                        WHERE
                            fingerprint =
                                :fingerprint;
                        """
                    ),
                    {
                        "fingerprint":
                            fingerprint,
                    },
                )
                .mappings()
                .first()
            )

            payload_json = json.dumps(
                priority,
                default=str,
            )

            # ------------------------------------------------
            # NEW INSIGHT
            # ------------------------------------------------

            if existing is None:

                row = (
                    connection.execute(
                        text(
                            """
                            INSERT INTO
                                analytics.business_insights
                            (
                                fingerprint,
                                title,
                                insight_type,
                                dimension,
                                dimension_value,
                                primary_metric,
                                diagnosis,
                                severity,
                                priority_score,
                                lifecycle_status,
                                period_start,
                                period_end,
                                comparison_start,
                                comparison_end,
                                payload
                            )
                            VALUES
                            (
                                :fingerprint,
                                :title,
                                :insight_type,
                                :dimension,
                                :dimension_value,
                                :primary_metric,
                                :diagnosis,
                                :severity,
                                :priority_score,
                                'NEW',
                                :period_start,
                                :period_end,
                                :comparison_start,
                                :comparison_end,
                                CAST(
                                    :payload
                                    AS JSONB
                                )
                            )
                            RETURNING
                                *;
                            """
                        ),
                        {
                            "fingerprint":
                                fingerprint,

                            "title":
                                priority[
                                    "title"
                                ],

                            "insight_type":
                                priority[
                                    "type"
                                ],

                            "dimension":
                                priority[
                                    "dimension"
                                ],

                            "dimension_value":
                                priority[
                                    "entity"
                                ],

                            "primary_metric":
                                priority[
                                    "primary_metric"
                                ],

                            "diagnosis":
                                priority.get(
                                    "diagnosis"
                                ),

                            "severity":
                                priority.get(
                                    "severity"
                                )
                                or
                                "low",

                            "priority_score":
                                priority[
                                    "priority_score"
                                ],

                            "period_start":
                                period_start,

                            "period_end":
                                period_end,

                            "comparison_start":
                                comparison_start,

                            "comparison_end":
                                comparison_end,

                            "payload":
                                payload_json,
                        },
                    )
                    .mappings()
                    .one()
                )

            # ------------------------------------------------
            # EXISTING INSIGHT
            # ------------------------------------------------

            else:

                existing_dict = dict(
                    existing
                )

                same_cycle = (
                    is_same_cycle(
                        existing=
                            existing_dict,

                        period_start=
                            period_start,

                        period_end=
                            period_end,

                        comparison_start=
                            comparison_start,

                        comparison_end=
                            comparison_end,
                    )
                )

                lifecycle_status = (
                    next_status(
                        existing=
                            existing_dict,

                        priority=
                            priority,

                        same_cycle=
                            same_cycle,
                    )
                )

                # ------------------------------------------------
                # occurrence_count increments only when the issue
                # survives into a genuinely new analytical period
                # or when a resolved issue reappears.
                # ------------------------------------------------

                occurrence_increment = (
                    0
                    if
                    same_cycle
                    else
                    1
                )

                row = (
                    connection.execute(
                        text(
                            """
                            UPDATE
                                analytics.business_insights

                            SET
                                title =
                                    :title,

                                insight_type =
                                    :insight_type,

                                dimension =
                                    :dimension,

                                dimension_value =
                                    :dimension_value,

                                primary_metric =
                                    :primary_metric,

                                diagnosis =
                                    :diagnosis,

                                severity =
                                    :severity,

                                priority_score =
                                    :priority_score,

                                lifecycle_status =
                                    :lifecycle_status,

                                period_start =
                                    :period_start,

                                period_end =
                                    :period_end,

                                comparison_start =
                                    :comparison_start,

                                comparison_end =
                                    :comparison_end,

                                last_detected_at =
                                    NOW(),

                                resolved_at =
                                    NULL,

                                occurrence_count =
                                    occurrence_count
                                    +
                                    :occurrence_increment,

                                payload =
                                    CAST(
                                        :payload
                                        AS JSONB
                                    ),

                                updated_at =
                                    NOW()

                            WHERE
                                fingerprint =
                                    :fingerprint

                            RETURNING
                                *;
                            """
                        ),
                        {
                            "fingerprint":
                                fingerprint,

                            "title":
                                priority[
                                    "title"
                                ],

                            "insight_type":
                                priority[
                                    "type"
                                ],

                            "dimension":
                                priority[
                                    "dimension"
                                ],

                            "dimension_value":
                                priority[
                                    "entity"
                                ],

                            "primary_metric":
                                priority[
                                    "primary_metric"
                                ],

                            "diagnosis":
                                priority.get(
                                    "diagnosis"
                                ),

                            "severity":
                                priority.get(
                                    "severity"
                                )
                                or
                                "low",

                            "priority_score":
                                priority[
                                    "priority_score"
                                ],

                            "lifecycle_status":
                                lifecycle_status,

                            "period_start":
                                period_start,

                            "period_end":
                                period_end,

                            "comparison_start":
                                comparison_start,

                            "comparison_end":
                                comparison_end,

                            "occurrence_increment":
                                occurrence_increment,

                            "payload":
                                payload_json,
                        },
                    )
                    .mappings()
                    .one()
                )

            saved[
                fingerprint
            ] = (
                row_to_dict(
                    row
                )
            )

        # ----------------------------------------------------
        # RESOLVE INSIGHTS THAT DISAPPEARED
        # ----------------------------------------------------

        active_rows = (
            connection.execute(
                text(
                    """
                    SELECT
                        fingerprint
                    FROM
                        analytics.business_insights
                    WHERE
                        lifecycle_status
                        <>
                        'RESOLVED';
                    """
                )
            )
            .scalars()
            .all()
        )

        for fingerprint in (
            active_rows
        ):

            if fingerprint in (
                seen_fingerprints
            ):

                continue

            connection.execute(
                text(
                    """
                    UPDATE
                        analytics.business_insights

                    SET
                        lifecycle_status =
                            'RESOLVED',

                        resolved_at =
                            NOW(),

                        updated_at =
                            NOW()

                    WHERE
                        fingerprint =
                            :fingerprint;
                    """
                ),
                {
                    "fingerprint":
                        fingerprint,
                },
            )

    return saved


# ============================================================
# ACTIVE INSIGHTS
# ============================================================

def get_active_insights() -> list[dict]:

    query = text(
        """
        SELECT
            *
        FROM
            analytics.business_insights
        WHERE
            lifecycle_status
            <>
            'RESOLVED'
        ORDER BY
            CASE
                WHEN
                    insight_type = 'risk'
                THEN
                    0
                ELSE
                    1
            END,

            priority_score DESC;
        """
    )

    with engine.connect() as connection:

        rows = (
            connection.execute(
                query
            )
            .mappings()
            .all()
        )

    return [
        row_to_dict(
            row
        )
        for row
        in rows
    ]


# ============================================================
# ALL INSIGHTS
# ============================================================

def get_all_insights() -> list[dict]:

    query = text(
        """
        SELECT
            *
        FROM
            analytics.business_insights
        ORDER BY
            updated_at DESC,
            priority_score DESC;
        """
    )

    with engine.connect() as connection:

        rows = (
            connection.execute(
                query
            )
            .mappings()
            .all()
        )

    return [
        row_to_dict(
            row
        )
        for row
        in rows
    ]


# ============================================================
# SINGLE INSIGHT
# ============================================================

def get_insight(
    insight_id: int,
) -> dict:

    query = text(
        """
        SELECT
            *
        FROM
            analytics.business_insights
        WHERE
            insight_id =
                :insight_id;
        """
    )

    with engine.connect() as connection:

        row = (
            connection.execute(
                query,
                {
                    "insight_id":
                        insight_id,
                },
            )
            .mappings()
            .first()
        )

    if row is None:

        raise ValueError(
            f"Insight {insight_id} was not found."
        )

    return (
        row_to_dict(
            row
        )
    )