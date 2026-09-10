from __future__ import annotations

import calendar
import json

from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy import text

from ..database import engine


# ============================================================
# SUPPORTED METRICS
# ============================================================

SUPPORTED_METRICS = {
    "net_sales",
    "gross_profit",
    "margin_pct",
    "units_sold",
    "transactions",
    "avg_selling_price",
    "discount_pct",
    "cost_per_unit",
}


# ============================================================
# SUPPORTED DIMENSIONS
# ============================================================

SUPPORTED_DIMENSIONS = {
    "overall",
    "region",
    "city",
    "channel",
}


DIMENSION_COLUMNS = {
    "region":
        "s.region",

    "city":
        "s.city",

    "channel":
        "s.channel",
}


# ============================================================
# METRIC DIRECTION POLICY
# ============================================================

LOWER_IS_BETTER = {
    "discount_pct",
    "cost_per_unit",
    "stockout_rate",
}


PERCENTAGE_POINT_METRICS = {
    "margin_pct",
    "discount_pct",
    "stockout_rate",
}


DEFAULT_CHANGE_THRESHOLD_PCT = 2.0

DEFAULT_CHANGE_THRESHOLD_PP = 0.25


# ============================================================
# JSON SAFE
# ============================================================

def json_safe(
    value: Any,
) -> Any:

    if isinstance(
        value,
        Decimal,
    ):

        return float(
            value
        )

    if isinstance(
        value,
        date,
    ):

        return value.isoformat()

    if isinstance(
        value,
        dict,
    ):

        return {
            str(key):
                json_safe(
                    item
                )

            for (
                key,
                item,
            )
            in value.items()
        }

    if isinstance(
        value,
        (
            list,
            tuple,
        ),
    ):

        return [
            json_safe(
                item
            )

            for item
            in value
        ]

    return value


# ============================================================
# SAFE FLOAT
# ============================================================

def safe_float(
    value: Any,
) -> float | None:

    if value is None:

        return None

    if isinstance(
        value,
        bool,
    ):

        return None

    try:

        return float(
            value
        )

    except (
        TypeError,
        ValueError,
    ):

        return None


# ============================================================
# MONTH HELPERS
# ============================================================

def month_start(
    value: date,
) -> date:

    return value.replace(
        day=1
    )


def month_end(
    value: date,
) -> date:

    final_day = (
        calendar.monthrange(
            value.year,
            value.month,
        )[1]
    )

    return value.replace(
        day=final_day
    )


def previous_month_end(
    value: date,
) -> date:

    first_day = (
        month_start(
            value
        )
    )

    if (
        first_day.month
        ==
        1
    ):

        return date(
            first_day.year
            -
            1,
            12,
            31,
        )

    previous_month = date(
        first_day.year,
        first_day.month
        -
        1,
        1,
    )

    return month_end(
        previous_month
    )


# ============================================================
# LATEST DATA DATE
# ============================================================

def get_latest_data_date() -> date | None:

    query = text(
        """
        SELECT
            MAX(date_id)

        FROM
            analytics.fact_sales_daily;
        """
    )

    with engine.connect() as connection:

        return (
            connection
            .execute(
                query
            )
            .scalar_one_or_none()
        )


# ============================================================
# LATEST COMPLETE MONTH
# ============================================================

def get_latest_complete_month() -> tuple[
    date,
    date,
] | None:

    latest_date = (
        get_latest_data_date()
    )

    if latest_date is None:

        return None

    if (
        latest_date
        ==
        month_end(
            latest_date
        )
    ):

        evaluation_end = (
            latest_date
        )

    else:

        evaluation_end = (
            previous_month_end(
                latest_date
            )
        )

    evaluation_start = (
        month_start(
            evaluation_end
        )
    )

    return (
        evaluation_start,
        evaluation_end,
    )


# ============================================================
# ACTION CONTEXT
# ============================================================

def get_action_context(
    action_id: int,
) -> dict:

    query = text(
        """
        SELECT
            a.action_id,
            a.insight_id,

            a.title
                AS action_title,

            a.owner_name,

            a.status
                AS action_status,

            a.due_date,

            a.notes
                AS action_notes,

            a.created_at
                AS action_created_at,

            a.updated_at
                AS action_updated_at,

            a.completed_at,

            i.title
                AS insight_title,

            i.insight_type,
            i.dimension,
            i.dimension_value,
            i.primary_metric,
            i.severity,
            i.priority_score,
            i.lifecycle_status,
            i.period_start,
            i.period_end

        FROM
            analytics.insight_actions a

        INNER JOIN
            analytics.business_insights i

            ON
                i.insight_id =
                a.insight_id

        WHERE
            a.action_id =
            :action_id;
        """
    )

    with engine.connect() as connection:

        row = (
            connection
            .execute(
                query,
                {
                    "action_id":
                        action_id,
                },
            )
            .mappings()
            .one_or_none()
        )

    if row is None:

        raise KeyError(
            (
                "Action "
                f"{action_id} "
                "was not found."
            )
        )

    return dict(
        row
    )


# ============================================================
# LIST ACTION IDS
#
# We deliberately filter status in Python.
#
# This avoids PostgreSQL-array parameter edge cases and keeps
# the function robust across psycopg / SQLAlchemy versions.
# ============================================================

def list_action_ids(
    statuses: tuple[str, ...] = (
        "COMPLETED",
        "IN_PROGRESS",
    ),
) -> list[int]:

    normalized_statuses = {
        str(status)
        .strip()
        .upper()

        for status
        in statuses

        if str(status).strip()
    }

    if not normalized_statuses:

        return []

    query = text(
        """
        SELECT
            action_id,
            status

        FROM
            analytics.insight_actions

        ORDER BY
            action_id;
        """
    )

    with engine.connect() as connection:

        rows = (
            connection
            .execute(
                query
            )
            .mappings()
            .all()
        )

    result: list[int] = []

    for row in rows:

        status = (
            str(
                row.get(
                    "status"
                )
                or
                ""
            )
            .strip()
            .upper()
        )

        if (
            status
            in
            normalized_statuses
        ):

            result.append(
                int(
                    row[
                        "action_id"
                    ]
                )
            )

    return result


# ============================================================
# SALES METRIC SNAPSHOT
# ============================================================

def get_sales_metric_snapshot(
    start_date: date,
    end_date: date,
    dimension: str,
    dimension_value: str | None,
) -> dict[str, float | None]:

    normalized_dimension = (
        str(
            dimension
            or
            "overall"
        )
        .strip()
        .lower()
    )

    if (
        normalized_dimension
        not in
        SUPPORTED_DIMENSIONS
    ):

        raise ValueError(
            (
                "Action Effectiveness V1 does not "
                "support dimension "
                f"'{dimension}'."
            )
        )

    parameters: dict[str, Any] = {
        "start_date":
            start_date,

        "end_date":
            end_date,
    }

    where_filter = ""

    if (
        normalized_dimension
        !=
        "overall"
    ):

        if not dimension_value:

            raise ValueError(
                (
                    "A dimension value is required "
                    f"for '{normalized_dimension}'."
                )
            )

        column = (
            DIMENSION_COLUMNS[
                normalized_dimension
            ]
        )

        where_filter = (
            f"""
            AND
                {column} =
                :dimension_value
            """
        )

        parameters[
            "dimension_value"
        ] = dimension_value

    query = text(
        f"""
        SELECT
            SUM(
                f.net_sales
            )
                AS net_sales,

            SUM(
                f.units_sold
            )
                AS units_sold,

            SUM(
                f.transactions
            )
                AS transactions,

            SUM(
                f.net_sales
                -
                f.cogs
            )
                AS gross_profit,

            CASE

                WHEN
                    SUM(
                        f.net_sales
                    )
                    =
                    0

                THEN
                    NULL

                ELSE
                    (
                        SUM(
                            f.net_sales
                            -
                            f.cogs
                        )
                        /
                        SUM(
                            f.net_sales
                        )
                    )
                    *
                    100

            END
                AS margin_pct,

            CASE

                WHEN
                    SUM(
                        f.units_sold
                    )
                    =
                    0

                THEN
                    NULL

                ELSE
                    SUM(
                        f.net_sales
                    )
                    /
                    SUM(
                        f.units_sold
                    )

            END
                AS avg_selling_price,

            CASE

                WHEN
                    SUM(
                        f.gross_sales
                    )
                    =
                    0

                THEN
                    NULL

                ELSE
                    (
                        SUM(
                            f.discount_amount
                        )
                        /
                        SUM(
                            f.gross_sales
                        )
                    )
                    *
                    100

            END
                AS discount_pct,

            CASE

                WHEN
                    SUM(
                        f.units_sold
                    )
                    =
                    0

                THEN
                    NULL

                ELSE
                    SUM(
                        f.cogs
                    )
                    /
                    SUM(
                        f.units_sold
                    )

            END
                AS cost_per_unit

        FROM
            analytics.fact_sales_daily f

        INNER JOIN
            analytics.dim_store s

            ON
                s.store_id =
                f.store_id

        WHERE
            f.date_id
            BETWEEN
                :start_date
                AND
                :end_date

        {where_filter};
        """
    )

    with engine.connect() as connection:

        row = (
            connection
            .execute(
                query,
                parameters,
            )
            .mappings()
            .one()
        )

    return {
        key:
            safe_float(
                value
            )

        for (
            key,
            value,
        )
        in row.items()
    }


# ============================================================
# DESIRED DIRECTION
# ============================================================

def determine_desired_direction(
    metric: str,
    insight_type: str | None = None,
) -> str:

    del insight_type

    normalized_metric = (
        str(
            metric
        )
        .strip()
        .lower()
    )

    if (
        normalized_metric
        in
        LOWER_IS_BETTER
    ):

        return "DECREASE"

    return "INCREASE"


# ============================================================
# EFFECTIVENESS CLASSIFICATION
# ============================================================

def classify_effectiveness(
    metric: str,
    baseline_value: float,
    current_value: float,
    desired_direction: str,
    pct_threshold: float = (
        DEFAULT_CHANGE_THRESHOLD_PCT
    ),
    pp_threshold: float = (
        DEFAULT_CHANGE_THRESHOLD_PP
    ),
) -> dict:

    normalized_metric = (
        str(
            metric
        )
        .strip()
        .lower()
    )

    normalized_direction = (
        str(
            desired_direction
        )
        .strip()
        .upper()
    )

    if (
        normalized_direction
        not in
        {
            "INCREASE",
            "DECREASE",
            "MAINTAIN",
        }
    ):

        raise ValueError(
            (
                "Unsupported desired direction: "
                f"{desired_direction}"
            )
        )

    absolute_change = (
        current_value
        -
        baseline_value
    )

    if (
        baseline_value
        !=
        0
    ):

        change_pct = (
            absolute_change
            /
            abs(
                baseline_value
            )
            *
            100
        )

    else:

        change_pct = None

    change_pp = None

    if (
        normalized_metric
        in
        PERCENTAGE_POINT_METRICS
    ):

        change_pp = (
            absolute_change
        )

        raw_change = (
            change_pp
        )

        threshold = (
            pp_threshold
        )

        threshold_unit = (
            "percentage_points"
        )

    else:

        if (
            change_pct
            is not None
        ):

            raw_change = (
                change_pct
            )

            threshold = (
                pct_threshold
            )

            threshold_unit = (
                "percent"
            )

        else:

            raw_change = (
                absolute_change
            )

            threshold = 0.0

            threshold_unit = (
                "absolute"
            )

    if (
        normalized_direction
        ==
        "INCREASE"
    ):

        directional_change = (
            raw_change
        )

    elif (
        normalized_direction
        ==
        "DECREASE"
    ):

        directional_change = (
            -
            raw_change
        )

    else:

        directional_change = (
            -
            abs(
                raw_change
            )
        )

    if (
        normalized_direction
        ==
        "MAINTAIN"
    ):

        if (
            abs(
                raw_change
            )
            <=
            threshold
        ):

            status = (
                "UNCHANGED"
            )

        else:

            status = (
                "WORSENED"
            )

    elif (
        directional_change
        >
        threshold
    ):

        status = (
            "IMPROVED"
        )

    elif (
        directional_change
        <
        -
        threshold
    ):

        status = (
            "WORSENED"
        )

    else:

        status = (
            "UNCHANGED"
        )

    return {
        "effectiveness_status":
            status,

        "absolute_change":
            round(
                absolute_change,
                6,
            ),

        "change_pct":
            (
                round(
                    change_pct,
                    6,
                )

                if
                    change_pct
                    is not None

                else
                    None
            ),

        "change_pp":
            (
                round(
                    change_pp,
                    6,
                )

                if
                    change_pp
                    is not None

                else
                    None
            ),

        "desired_direction":
            normalized_direction,

        "directional_change":
            round(
                directional_change,
                6,
            ),

        "threshold":
            threshold,

        "threshold_unit":
            threshold_unit,
    }


# ============================================================
# SUMMARY
# ============================================================

def build_summary(
    metric: str,
    baseline_value: float,
    current_value: float,
    classification: dict,
) -> str:

    metric_label = (
        metric
        .replace(
            "_",
            " ",
        )
    )

    status = (
        classification[
            "effectiveness_status"
        ]
    )

    if (
        status
        ==
        "IMPROVED"
    ):

        movement_text = (
            "improved"
        )

    elif (
        status
        ==
        "WORSENED"
    ):

        movement_text = (
            "worsened"
        )

    else:

        movement_text = (
            "remained broadly unchanged"
        )

    return (
        f"The associated {metric_label} KPI "
        f"{movement_text} from "
        f"{baseline_value:.4f} to "
        f"{current_value:.4f}. "
        "This is period-over-period outcome "
        "tracking associated with a tracked "
        "management action. "
        "No causal attribution is claimed."
    )


# ============================================================
# NOT FOUND RESPONSE
# ============================================================

def action_not_found_response(
    action_id: int,
) -> dict:

    return {
        "status":
            "NOT_FOUND",

        "action_id":
            action_id,

        "insight_id":
            None,

        "causality_claimed":
            False,

        "persisted":
            False,

        "summary":
            (
                f"Action {action_id} does not exist "
                "in analytics.insight_actions."
            ),

        "evidence": {
            "reason":
                "action_not_found",
        },
    }


# ============================================================
# NOT READY RESPONSE
# ============================================================

def not_ready_response(
    context: dict,
    reason: str,
) -> dict:

    return {
        "status":
            "NOT_READY",

        "action_id":
            context.get(
                "action_id"
            ),

        "insight_id":
            context.get(
                "insight_id"
            ),

        "action_status":
            context.get(
                "action_status"
            ),

        "primary_metric":
            context.get(
                "primary_metric"
            ),

        "dimension":
            context.get(
                "dimension"
            ),

        "dimension_value":
            context.get(
                "dimension_value"
            ),

        "causality_claimed":
            False,

        "persisted":
            False,

        "summary":
            reason,

        "evidence": {
            "reason":
                reason,
        },
    }


# ============================================================
# UNSUPPORTED RESPONSE
# ============================================================

def unsupported_response(
    context: dict,
    reason: str,
) -> dict:

    return {
        "status":
            "UNSUPPORTED",

        "action_id":
            context.get(
                "action_id"
            ),

        "insight_id":
            context.get(
                "insight_id"
            ),

        "action_status":
            context.get(
                "action_status"
            ),

        "primary_metric":
            context.get(
                "primary_metric"
            ),

        "dimension":
            context.get(
                "dimension"
            ),

        "dimension_value":
            context.get(
                "dimension_value"
            ),

        "causality_claimed":
            False,

        "persisted":
            False,

        "summary":
            reason,

        "evidence": {
            "reason":
                reason,
        },
    }


# ============================================================
# PERSIST EVALUATION
# ============================================================

def persist_evaluation(
    evaluation: dict,
) -> int:

    query = text(
        """
        INSERT INTO
            analytics.action_effectiveness_evaluations
            (
                action_id,
                insight_id,
                evaluated_at,
                baseline_start,
                baseline_end,
                evaluation_start,
                evaluation_end,
                primary_metric,
                dimension,
                dimension_value,
                baseline_value,
                current_value,
                absolute_change,
                change_pct,
                change_pp,
                desired_direction,
                effectiveness_status,
                evaluation_basis,
                causality_claimed,
                summary,
                evidence
            )

        VALUES
            (
                :action_id,
                :insight_id,
                NOW(),
                :baseline_start,
                :baseline_end,
                :evaluation_start,
                :evaluation_end,
                :primary_metric,
                :dimension,
                :dimension_value,
                :baseline_value,
                :current_value,
                :absolute_change,
                :change_pct,
                :change_pp,
                :desired_direction,
                :effectiveness_status,
                :evaluation_basis,
                FALSE,
                :summary,
                CAST(
                    :evidence
                    AS JSONB
                )
            )

        ON CONFLICT
            (
                action_id,
                evaluation_end,
                primary_metric
            )

        DO UPDATE SET
            insight_id =
                EXCLUDED.insight_id,

            evaluated_at =
                NOW(),

            baseline_start =
                EXCLUDED.baseline_start,

            baseline_end =
                EXCLUDED.baseline_end,

            evaluation_start =
                EXCLUDED.evaluation_start,

            baseline_value =
                EXCLUDED.baseline_value,

            current_value =
                EXCLUDED.current_value,

            absolute_change =
                EXCLUDED.absolute_change,

            change_pct =
                EXCLUDED.change_pct,

            change_pp =
                EXCLUDED.change_pp,

            desired_direction =
                EXCLUDED.desired_direction,

            effectiveness_status =
                EXCLUDED.effectiveness_status,

            evaluation_basis =
                EXCLUDED.evaluation_basis,

            causality_claimed =
                FALSE,

            summary =
                EXCLUDED.summary,

            evidence =
                EXCLUDED.evidence

        RETURNING
            evaluation_id;
        """
    )

    parameters = {
        **evaluation,

        "evidence":
            json.dumps(
                json_safe(
                    evaluation[
                        "evidence"
                    ]
                )
            ),
    }

    with engine.begin() as connection:

        evaluation_id = (
            connection
            .execute(
                query,
                parameters,
            )
            .scalar_one()
        )

    return int(
        evaluation_id
    )


# ============================================================
# EVALUATE ONE ACTION
# ============================================================

def evaluate_action(
    action_id: int,
    persist: bool = True,
) -> dict:

    try:

        context = (
            get_action_context(
                action_id
            )
        )

    except KeyError:

        return (
            action_not_found_response(
                action_id
            )
        )

    metric = (
        str(
            context.get(
                "primary_metric"
            )
            or
            ""
        )
        .strip()
        .lower()
    )

    dimension = (
        str(
            context.get(
                "dimension"
            )
            or
            "overall"
        )
        .strip()
        .lower()
    )

    dimension_value = (
        context.get(
            "dimension_value"
        )
    )

    # --------------------------------------------------------
    # SUPPORTED METRIC
    # --------------------------------------------------------

    if (
        metric
        not in
        SUPPORTED_METRICS
    ):

        return (
            unsupported_response(
                context,
                (
                    "Action Effectiveness V1 does not "
                    f"yet support primary metric '{metric}'. "
                    "A dedicated KPI adapter is required."
                ),
            )
        )

    # --------------------------------------------------------
    # SUPPORTED DIMENSION
    # --------------------------------------------------------

    if (
        dimension
        not in
        SUPPORTED_DIMENSIONS
    ):

        return (
            unsupported_response(
                context,
                (
                    "Action Effectiveness V1 does not "
                    f"yet support dimension '{dimension}'."
                ),
            )
        )

    # --------------------------------------------------------
    # BASELINE PERIOD
    # --------------------------------------------------------

    baseline_start = (
        context.get(
            "period_start"
        )
    )

    baseline_end = (
        context.get(
            "period_end"
        )
    )

    if (
        baseline_start
        is None

        or

        baseline_end
        is None
    ):

        return (
            unsupported_response(
                context,
                (
                    "The linked business insight does "
                    "not contain a usable baseline period."
                ),
            )
        )

    # --------------------------------------------------------
    # LATEST COMPLETE PERIOD
    # --------------------------------------------------------

    latest_period = (
        get_latest_complete_month()
    )

    if latest_period is None:

        return (
            not_ready_response(
                context,
                (
                    "No complete warehouse period is "
                    "currently available for evaluation."
                ),
            )
        )

    (
        evaluation_start,
        evaluation_end,
    ) = latest_period

    if (
        evaluation_end
        <=
        baseline_end
    ):

        return (
            not_ready_response(
                context,
                (
                    "The warehouse has not yet advanced "
                    "beyond the action baseline period. "
                    f"Baseline ends {baseline_end}; "
                    f"latest complete data ends "
                    f"{evaluation_end}."
                ),
            )
        )

    # --------------------------------------------------------
    # BASELINE KPI SNAPSHOT
    # --------------------------------------------------------

    baseline_snapshot = (
        get_sales_metric_snapshot(
            start_date=
                baseline_start,

            end_date=
                baseline_end,

            dimension=
                dimension,

            dimension_value=
                dimension_value,
        )
    )

    # --------------------------------------------------------
    # CURRENT KPI SNAPSHOT
    # --------------------------------------------------------

    current_snapshot = (
        get_sales_metric_snapshot(
            start_date=
                evaluation_start,

            end_date=
                evaluation_end,

            dimension=
                dimension,

            dimension_value=
                dimension_value,
        )
    )

    baseline_value = (
        baseline_snapshot.get(
            metric
        )
    )

    current_value = (
        current_snapshot.get(
            metric
        )
    )

    if (
        baseline_value
        is None

        or

        current_value
        is None
    ):

        return (
            unsupported_response(
                context,
                (
                    "The selected KPI could not be "
                    "calculated for both evaluation periods."
                ),
            )
        )

    # --------------------------------------------------------
    # DIRECTION
    # --------------------------------------------------------

    desired_direction = (
        determine_desired_direction(
            metric=
                metric,

            insight_type=
                context.get(
                    "insight_type"
                ),
        )
    )

    # --------------------------------------------------------
    # CLASSIFICATION
    # --------------------------------------------------------

    classification = (
        classify_effectiveness(
            metric=
                metric,

            baseline_value=
                baseline_value,

            current_value=
                current_value,

            desired_direction=
                desired_direction,
        )
    )

    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------

    summary = (
        build_summary(
            metric=
                metric,

            baseline_value=
                baseline_value,

            current_value=
                current_value,

            classification=
                classification,
        )
    )

    # --------------------------------------------------------
    # EVIDENCE
    # --------------------------------------------------------

    evidence = {
        "evaluation_basis":
            (
                "insight_period_to_latest_full_month"
            ),

        "causality_statement":
            (
                "Observed KPI movement is associated "
                "with the tracked action timeline. "
                "No causal attribution is claimed."
            ),

        "action": {
            "action_id":
                context[
                    "action_id"
                ],

            "title":
                context[
                    "action_title"
                ],

            "status":
                context[
                    "action_status"
                ],

            "created_at":
                json_safe(
                    context[
                        "action_created_at"
                    ]
                ),

            "completed_at":
                json_safe(
                    context[
                        "completed_at"
                    ]
                ),
        },

        "insight": {
            "insight_id":
                context[
                    "insight_id"
                ],

            "title":
                context[
                    "insight_title"
                ],

            "type":
                context[
                    "insight_type"
                ],

            "severity":
                context[
                    "severity"
                ],

            "priority_score":
                json_safe(
                    context[
                        "priority_score"
                    ]
                ),

            "lifecycle_status":
                context[
                    "lifecycle_status"
                ],
        },

        "scope": {
            "dimension":
                dimension,

            "dimension_value":
                dimension_value,
        },

        "baseline_period": {
            "start":
                baseline_start.isoformat(),

            "end":
                baseline_end.isoformat(),
        },

        "evaluation_period": {
            "start":
                evaluation_start.isoformat(),

            "end":
                evaluation_end.isoformat(),
        },

        "baseline_snapshot":
            baseline_snapshot,

        "current_snapshot":
            current_snapshot,

        "classification":
            classification,
    }

    # --------------------------------------------------------
    # EVALUATION RECORD
    # --------------------------------------------------------

    evaluation = {
        "action_id":
            int(
                context[
                    "action_id"
                ]
            ),

        "insight_id":
            int(
                context[
                    "insight_id"
                ]
            ),

        "baseline_start":
            baseline_start,

        "baseline_end":
            baseline_end,

        "evaluation_start":
            evaluation_start,

        "evaluation_end":
            evaluation_end,

        "primary_metric":
            metric,

        "dimension":
            dimension,

        "dimension_value":
            dimension_value,

        "baseline_value":
            baseline_value,

        "current_value":
            current_value,

        "absolute_change":
            classification[
                "absolute_change"
            ],

        "change_pct":
            classification[
                "change_pct"
            ],

        "change_pp":
            classification[
                "change_pp"
            ],

        "desired_direction":
            classification[
                "desired_direction"
            ],

        "effectiveness_status":
            classification[
                "effectiveness_status"
            ],

        "evaluation_basis":
            (
                "insight_period_to_latest_full_month"
            ),

        "summary":
            summary,

        "evidence":
            evidence,
    }

    # --------------------------------------------------------
    # PERSIST
    # --------------------------------------------------------

    evaluation_id = None

    if persist:

        evaluation_id = (
            persist_evaluation(
                evaluation
            )
        )

    # --------------------------------------------------------
    # RESPONSE
    # --------------------------------------------------------

    return {
        "status":
            classification[
                "effectiveness_status"
            ],

        "evaluation_id":
            evaluation_id,

        "action_id":
            evaluation[
                "action_id"
            ],

        "insight_id":
            evaluation[
                "insight_id"
            ],

        "action_status":
            context[
                "action_status"
            ],

        "primary_metric":
            metric,

        "dimension":
            dimension,

        "dimension_value":
            dimension_value,

        "baseline_start":
            baseline_start.isoformat(),

        "baseline_end":
            baseline_end.isoformat(),

        "evaluation_start":
            evaluation_start.isoformat(),

        "evaluation_end":
            evaluation_end.isoformat(),

        "baseline_value":
            round(
                baseline_value,
                6,
            ),

        "current_value":
            round(
                current_value,
                6,
            ),

        "absolute_change":
            classification[
                "absolute_change"
            ],

        "change_pct":
            classification[
                "change_pct"
            ],

        "change_pp":
            classification[
                "change_pp"
            ],

        "desired_direction":
            classification[
                "desired_direction"
            ],

        "causality_claimed":
            False,

        "persisted":
            bool(
                persist
            ),

        "summary":
            summary,

        "evidence":
            json_safe(
                evidence
            ),
    }


# ============================================================
# EVALUATE MULTIPLE ACTIONS
# ============================================================

def evaluate_actions(
    statuses: tuple[str, ...] = (
        "COMPLETED",
        "IN_PROGRESS",
    ),
    persist: bool = True,
) -> dict:

    action_ids = (
        list_action_ids(
            statuses=
                statuses
        )
    )

    # --------------------------------------------------------
    # EMPTY ACTION TRACKER
    # --------------------------------------------------------

    if not action_ids:

        return {
            "status":
                "NO_ACTIONS",

            "actions_considered":
                0,

            "persist":
                persist,

            "status_counts":
                {},

            "results":
                [],

            "summary":
                (
                    "No tracked management actions match "
                    "the requested statuses. Create an "
                    "action first, then rerun the "
                    "effectiveness evaluator."
                ),
        }

    # --------------------------------------------------------
    # RUN EVALUATIONS
    # --------------------------------------------------------

    results: list[dict] = []

    for action_id in action_ids:

        try:

            result = (
                evaluate_action(
                    action_id=
                        action_id,

                    persist=
                        persist,
                )
            )

        except Exception as error:

            result = {
                "status":
                    "ERROR",

                "action_id":
                    action_id,

                "causality_claimed":
                    False,

                "persisted":
                    False,

                "summary":
                    (
                        f"{type(error).__name__}: "
                        f"{str(error)}"
                    ),
            }

        results.append(
            result
        )

    # --------------------------------------------------------
    # STATUS COUNTS
    # --------------------------------------------------------

    counts: dict[str, int] = {}

    for result in results:

        status = (
            str(
                result.get(
                    "status"
                )
                or
                "UNKNOWN"
            )
        )

        counts[
            status
        ] = (
            counts.get(
                status,
                0,
            )
            +
            1
        )

    return {
        "status":
            "success",

        "actions_considered":
            len(
                action_ids
            ),

        "persist":
            persist,

        "status_counts":
            counts,

        "results":
            results,
    }