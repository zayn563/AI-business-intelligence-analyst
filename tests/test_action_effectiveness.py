from datetime import date

from sqlalchemy import text

from backend.app.database import engine

from backend.app.decision.action_effectiveness import (
    classify_effectiveness,
    determine_desired_direction,
    evaluate_action,
    get_latest_complete_month,
    month_end,
    month_start,
)


# ============================================================
# MONTH HELPERS
# ============================================================

def test_month_helpers():

    value = date(
        2026,
        8,
        15,
    )

    assert (
        month_start(
            value
        )
        ==
        date(
            2026,
            8,
            1,
        )
    )

    assert (
        month_end(
            value
        )
        ==
        date(
            2026,
            8,
            31,
        )
    )


# ============================================================
# INCREASE IS BETTER
# ============================================================

def test_increase_metric_improved():

    result = (
        classify_effectiveness(
            metric=
                "net_sales",

            baseline_value=
                100.0,

            current_value=
                110.0,

            desired_direction=
                "INCREASE",
        )
    )

    assert (
        result[
            "effectiveness_status"
        ]
        ==
        "IMPROVED"
    )

    assert (
        result[
            "change_pct"
        ]
        ==
        10.0
    )


# ============================================================
# INCREASE METRIC WORSENED
# ============================================================

def test_increase_metric_worsened():

    result = (
        classify_effectiveness(
            metric=
                "gross_profit",

            baseline_value=
                100.0,

            current_value=
                90.0,

            desired_direction=
                "INCREASE",
        )
    )

    assert (
        result[
            "effectiveness_status"
        ]
        ==
        "WORSENED"
    )


# ============================================================
# LOWER IS BETTER
# ============================================================

def test_lower_metric_improved():

    result = (
        classify_effectiveness(
            metric=
                "cost_per_unit",

            baseline_value=
                10.0,

            current_value=
                9.0,

            desired_direction=
                "DECREASE",
        )
    )

    assert (
        result[
            "effectiveness_status"
        ]
        ==
        "IMPROVED"
    )


# ============================================================
# PERCENTAGE POINT METRIC
# ============================================================

def test_margin_percentage_point_improved():

    result = (
        classify_effectiveness(
            metric=
                "margin_pct",

            baseline_value=
                32.0,

            current_value=
                36.0,

            desired_direction=
                "INCREASE",
        )
    )

    assert (
        result[
            "effectiveness_status"
        ]
        ==
        "IMPROVED"
    )

    assert (
        result[
            "change_pp"
        ]
        ==
        4.0
    )


# ============================================================
# MATERIALITY / UNCHANGED
# ============================================================

def test_small_change_is_unchanged():

    result = (
        classify_effectiveness(
            metric=
                "net_sales",

            baseline_value=
                100.0,

            current_value=
                101.0,

            desired_direction=
                "INCREASE",
        )
    )

    assert (
        result[
            "effectiveness_status"
        ]
        ==
        "UNCHANGED"
    )


# ============================================================
# DIRECTION POLICY
# ============================================================

def test_direction_policy():

    assert (
        determine_desired_direction(
            "net_sales"
        )
        ==
        "INCREASE"
    )

    assert (
        determine_desired_direction(
            "gross_profit"
        )
        ==
        "INCREASE"
    )

    assert (
        determine_desired_direction(
            "discount_pct"
        )
        ==
        "DECREASE"
    )

    assert (
        determine_desired_direction(
            "cost_per_unit"
        )
        ==
        "DECREASE"
    )


# ============================================================
# SCHEMA EXISTS
# ============================================================

def test_action_effectiveness_table_exists():

    with engine.connect() as connection:

        relation = (
            connection
            .execute(
                text(
                    """
                    SELECT
                        TO_REGCLASS(
                            'analytics.action_effectiveness_evaluations'
                        );
                    """
                )
            )
            .scalar_one_or_none()
        )

    assert (
        relation
        ==
        (
            "analytics."
            "action_effectiveness_evaluations"
        )
    )


# ============================================================
# LATEST COMPLETE MONTH
# ============================================================

def test_latest_complete_month_exists():

    result = (
        get_latest_complete_month()
    )

    assert (
        result
        is not None
    )

    (
        start,
        end,
    ) = result

    assert (
        start.day
        ==
        1
    )

    assert (
        end
        ==
        month_end(
            end
        )
    )


# ============================================================
# MISSING ACTION SHOULD NOT THROW TRACEBACK
# ============================================================

def test_missing_action_returns_structured_not_found():

    result = (
        evaluate_action(
            action_id=
                999999999,

            persist=
                False,
        )
    )

    assert (
        result[
            "status"
        ]
        ==
        "NOT_FOUND"
    )

    assert (
        result[
            "causality_claimed"
        ]
        is
        False
    )

    assert (
        result[
            "persisted"
        ]
        is
        False
    )