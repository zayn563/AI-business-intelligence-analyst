from __future__ import annotations

from datetime import (
    date,
)

from typing import Any

from sqlalchemy import (
    text,
)

from ..database import (
    engine,
)

from ..data_quality import (
    get_data_freshness_report,
)

from ..decision.brief_service import (
    build_business_brief,
)

from ..decision.insight_service import (
    get_active_insights,
)

from ..intelligence.intelligence_service import (
    latest_complete_periods,
)

from ..intelligence.target_analysis import (
    analyze_targets,
)


# ============================================================
# HELPERS
# ============================================================

def as_float(
    value: Any,
) -> float | None:

    if value is None:

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


def percent_change(
    current: float | None,
    previous: float | None,
) -> float | None:

    if (
        current is None
        or
        previous is None
        or
        previous == 0
    ):

        return None

    return round(
        (
            (
                current
                -
                previous
            )
            /
            abs(
                previous
            )
        )
        *
        100.0,
        2,
    )


def direction_from_change(
    value: float | None,
) -> str:

    if value is None:

        return "unknown"

    if value > 0:

        return "increase"

    if value < 0:

        return "decrease"

    return "unchanged"


def shift_month(
    value: date,
    offset: int,
) -> date:

    month_index = (
        value.year
        *
        12
        +
        value.month
        -
        1
        +
        offset
    )

    year = (
        month_index
        //
        12
    )

    month = (
        month_index
        %
        12
        +
        1
    )

    return date(
        year,
        month,
        1,
    )


def unique_text_values(
    values,
) -> list[str]:

    result: list[str] = []

    seen: set[str] = set()

    for value in (
        values
        or
        []
    ):

        text_value = (
            str(
                value
            )
            .strip()
        )

        if (
            not text_value
            or
            text_value
            in
            seen
        ):

            continue

        seen.add(
            text_value
        )

        result.append(
            text_value
        )

    return result


# ============================================================
# LATEST SALES DATE
# ============================================================

def get_latest_sales_date() -> date:

    query = text(
        """
        SELECT
            MAX(
                date_id
            )
        FROM
            analytics.fact_sales_daily;
        """
    )

    with engine.connect() as connection:

        latest_date = (
            connection
            .execute(
                query
            )
            .scalar_one()
        )

    if latest_date is None:

        raise ValueError(
            "No sales data is available."
        )

    return latest_date


# ============================================================
# PERIOD AGGREGATION
# ============================================================

def aggregate_period(
    start_date: date,
    end_date: date,
) -> dict:

    query = text(
        """
        SELECT
            COALESCE(
                SUM(
                    net_sales
                ),
                0
            ) AS net_sales,

            COALESCE(
                SUM(
                    units_sold
                ),
                0
            ) AS units_sold,

            COALESCE(
                SUM(
                    transactions
                ),
                0
            ) AS transactions,

            COALESCE(
                SUM(
                    net_sales
                    -
                    cogs
                ),
                0
            ) AS gross_profit

        FROM
            analytics.fact_sales_daily

        WHERE
            date_id
            BETWEEN
                :start_date
                AND
                :end_date;
        """
    )

    with engine.connect() as connection:

        row = (
            connection
            .execute(
                query,
                {
                    "start_date":
                        start_date,

                    "end_date":
                        end_date,
                },
            )
            .mappings()
            .one()
        )

    net_sales = (
        as_float(
            row[
                "net_sales"
            ]
        )
        or
        0.0
    )

    units_sold = (
        as_float(
            row[
                "units_sold"
            ]
        )
        or
        0.0
    )

    transactions = (
        as_float(
            row[
                "transactions"
            ]
        )
        or
        0.0
    )

    gross_profit = (
        as_float(
            row[
                "gross_profit"
            ]
        )
        or
        0.0
    )

    margin_pct = (
        (
            gross_profit
            /
            net_sales
        )
        *
        100.0
        if net_sales
        else
        None
    )

    return {

        "net_sales":
            round(
                net_sales,
                2,
            ),

        "units_sold":
            round(
                units_sold,
                2,
            ),

        "transactions":
            round(
                transactions,
                2,
            ),

        "gross_profit":
            round(
                gross_profit,
                2,
            ),

        "margin_pct":
            (
                round(
                    margin_pct,
                    2,
                )
                if
                margin_pct
                is not None
                else
                None
            ),
    }


# ============================================================
# KPI COMPARISON
# ============================================================

def comparison_kpi(
    label: str,
    current: float | None,
    previous: float | None,
    unit: str,
    use_percentage_points: bool = False,
) -> dict:

    if use_percentage_points:

        change_pp = (
            (
                current
                -
                previous
            )
            if
            current is not None
            and
            previous is not None
            else
            None
        )

        change_pp = (
            round(
                change_pp,
                2,
            )
            if
            change_pp is not None
            else
            None
        )

        return {

            "label":
                label,

            "current":
                current,

            "previous":
                previous,

            "change_pct":
                None,

            "change_pp":
                change_pp,

            "direction":
                direction_from_change(
                    change_pp
                ),

            "unit":
                unit,
        }

    change_pct = (
        percent_change(
            current,
            previous,
        )
    )

    return {

        "label":
            label,

        "current":
            current,

        "previous":
            previous,

        "change_pct":
            change_pct,

        "change_pp":
            None,

        "direction":
            direction_from_change(
                change_pct
            ),

        "unit":
            unit,
    }


# ============================================================
# TARGET ROW DISCOVERY
# ============================================================

def extract_target_rows(
    payload: Any,
) -> list[dict]:

    candidates: list[dict] = []

    def walk(
        value: Any,
    ) -> None:

        if isinstance(
            value,
            dict,
        ):

            region = (
                value.get(
                    "region"
                )
            )

            contains_target_data = any(
                key
                in
                value
                for key
                in (
                    "actual_sales",
                    "sales_target",
                    "sales_achievement_pct",
                )
            )

            if (
                region
                and
                contains_target_data
            ):

                candidates.append(
                    value
                )

            for child in (
                value.values()
            ):

                walk(
                    child
                )

        elif isinstance(
            value,
            list,
        ):

            for child in value:

                walk(
                    child
                )

    walk(
        payload
    )

    # The same regional target result can appear in more than
    # one section. Retain the richest record for each region.

    best_by_region: dict[
        str,
        dict,
    ] = {}

    for row in candidates:

        region = str(
            row.get(
                "region"
            )
        )

        score = sum(
            1
            for key
            in (
                "actual_sales",
                "sales_target",
                "sales_achievement_pct",
            )
            if
            row.get(
                key
            )
            is not None
        )

        current_best = (
            best_by_region.get(
                region
            )
        )

        if current_best is None:

            best_by_region[
                region
            ] = row

            continue

        current_score = sum(
            1
            for key
            in (
                "actual_sales",
                "sales_target",
                "sales_achievement_pct",
            )
            if
            current_best.get(
                key
            )
            is not None
        )

        if score > current_score:

            best_by_region[
                region
            ] = row

    return list(
        best_by_region.values()
    )


# ============================================================
# TARGET SUMMARY
# ============================================================

def build_target_summary(
    payload: dict,
) -> dict:

    rows = (
        extract_target_rows(
            payload
        )
    )

    actual_values = [
        as_float(
            row.get(
                "actual_sales"
            )
        )
        for row
        in rows
    ]

    target_values = [
        as_float(
            row.get(
                "sales_target"
            )
        )
        for row
        in rows
    ]

    actual_values = [
        value
        for value
        in actual_values
        if value is not None
    ]

    target_values = [
        value
        for value
        in target_values
        if value is not None
    ]

    actual_sales = (
        sum(
            actual_values
        )
        if
        actual_values
        else
        None
    )

    sales_target = (
        sum(
            target_values
        )
        if
        target_values
        else
        None
    )

    achievement = (
        (
            actual_sales
            /
            sales_target
        )
        *
        100.0
        if
        actual_sales is not None
        and
        sales_target
        not in {
            None,
            0,
        }
        else
        None
    )

    gap = (
        (
            actual_sales
            -
            sales_target
        )
        if
        actual_sales is not None
        and
        sales_target is not None
        else
        None
    )

    return {

        "label":
            "Target attainment",

        "current":
            (
                round(
                    achievement,
                    1,
                )
                if
                achievement is not None
                else
                None
            ),

        "actual_sales":
            (
                round(
                    actual_sales,
                    2,
                )
                if
                actual_sales is not None
                else
                None
            ),

        "sales_target":
            (
                round(
                    sales_target,
                    2,
                )
                if
                sales_target is not None
                else
                None
            ),

        "gap":
            (
                round(
                    gap,
                    2,
                )
                if
                gap is not None
                else
                None
            ),

        "unit":
            "percent",
    }


# ============================================================
# TARGET BY REGION
# ============================================================

def target_by_region(
    payload: dict,
) -> dict[str, float | None]:

    result: dict[
        str,
        float | None,
    ] = {}

    for row in (
        extract_target_rows(
            payload
        )
    ):

        region = (
            row.get(
                "region"
            )
        )

        if not region:

            continue

        achievement = (
            as_float(
                row.get(
                    "sales_achievement_pct"
                )
            )
        )

        if achievement is None:

            actual_sales = (
                as_float(
                    row.get(
                        "actual_sales"
                    )
                )
            )

            sales_target = (
                as_float(
                    row.get(
                        "sales_target"
                    )
                )
            )

            if (
                actual_sales is not None
                and
                sales_target
                not in {
                    None,
                    0,
                }
            ):

                achievement = (
                    actual_sales
                    /
                    sales_target
                    *
                    100.0
                )

        result[
            str(
                region
            )
        ] = (
            round(
                achievement,
                1,
            )
            if
            achievement is not None
            else
            None
        )

    return result


# ============================================================
# MONTHLY TREND
# ============================================================

def monthly_trend(
    current_month: date,
) -> list[dict]:

    trend_start = (
        shift_month(
            current_month,
            -6,
        )
    )

    trend_end = (
        shift_month(
            current_month,
            1,
        )
    )

    query = text(
        """
        SELECT
            DATE_TRUNC(
                'month',
                date_id
            )::date AS month,

            SUM(
                net_sales
            ) AS net_sales,

            SUM(
                units_sold
            ) AS units_sold,

            SUM(
                net_sales
                -
                cogs
            ) AS gross_profit

        FROM
            analytics.fact_sales_daily

        WHERE
            date_id
            >=
            :trend_start

            AND
            date_id
            <
            :trend_end

        GROUP BY
            1

        ORDER BY
            1;
        """
    )

    with engine.connect() as connection:

        rows = (
            connection
            .execute(
                query,
                {
                    "trend_start":
                        trend_start,

                    "trend_end":
                        trend_end,
                },
            )
            .mappings()
            .all()
        )

    result = []

    for row in rows:

        sales = (
            as_float(
                row[
                    "net_sales"
                ]
            )
            or
            0.0
        )

        gross_profit = (
            as_float(
                row[
                    "gross_profit"
                ]
            )
            or
            0.0
        )

        margin_pct = (
            (
                gross_profit
                /
                sales
            )
            *
            100.0
            if sales
            else
            None
        )

        result.append(
            {
                "month":
                    row[
                        "month"
                    ],

                "net_sales":
                    round(
                        sales,
                        2,
                    ),

                "gross_profit":
                    round(
                        gross_profit,
                        2,
                    ),

                "margin_pct":
                    (
                        round(
                            margin_pct,
                            2,
                        )
                        if
                        margin_pct is not None
                        else
                        None
                    ),

                "units_sold":
                    round(
                        (
                            as_float(
                                row[
                                    "units_sold"
                                ]
                            )
                            or
                            0.0
                        ),
                        2,
                    ),
            }
        )

    return result


# ============================================================
# REGION PERFORMANCE
# ============================================================

def region_performance(
    current_start: date,
    current_end: date,
    comparison_start: date,
    comparison_end: date,
    target_payload: dict,
) -> list[dict]:

    query = text(
        """
        SELECT
            s.region,

            SUM(
                CASE
                    WHEN
                        f.date_id
                        BETWEEN
                            :current_start
                            AND
                            :current_end
                    THEN
                        f.net_sales
                    ELSE
                        0
                END
            ) AS current_sales,

            SUM(
                CASE
                    WHEN
                        f.date_id
                        BETWEEN
                            :comparison_start
                            AND
                            :comparison_end
                    THEN
                        f.net_sales
                    ELSE
                        0
                END
            ) AS previous_sales

        FROM
            analytics.fact_sales_daily AS f

        INNER JOIN
            analytics.dim_store AS s
            ON
                s.store_id
                =
                f.store_id

        WHERE
            f.date_id
            BETWEEN
                :comparison_start
                AND
                :current_end

        GROUP BY
            s.region

        ORDER BY
            current_sales DESC;
        """
    )

    with engine.connect() as connection:

        rows = (
            connection
            .execute(
                query,
                {
                    "current_start":
                        current_start,

                    "current_end":
                        current_end,

                    "comparison_start":
                        comparison_start,

                    "comparison_end":
                        comparison_end,
                },
            )
            .mappings()
            .all()
        )

    regional_targets = (
        target_by_region(
            target_payload
        )
    )

    result = []

    for row in rows:

        region = str(
            row[
                "region"
            ]
        )

        current_sales = (
            as_float(
                row[
                    "current_sales"
                ]
            )
            or
            0.0
        )

        previous_sales = (
            as_float(
                row[
                    "previous_sales"
                ]
            )
            or
            0.0
        )

        result.append(
            {
                "region":
                    region,

                "net_sales":
                    round(
                        current_sales,
                        2,
                    ),

                "sales_change_pct":
                    percent_change(
                        current_sales,
                        previous_sales,
                    ),

                "target_attainment_pct":
                    regional_targets.get(
                        region
                    ),
            }
        )

    return result


# ============================================================
# EVIDENCE SUMMARY
# ============================================================

def build_evidence_summary(
    freshness: dict,
    active_insights: list[dict],
) -> dict:

    blocked_insights = [
        insight
        for insight
        in active_insights
        if insight.get(
            "resolution_blocked"
        )
        is True
    ]

    freshness_blockers = (
        freshness.get(
            "blocking_datasets"
        )
        or
        []
    )

    insight_blockers: list[str] = []

    for insight in blocked_insights:

        insight_blockers.extend(
            unique_text_values(
                insight.get(
                    "blocking_datasets"
                )
                or
                []
            )
        )

    blocking_datasets = (
        unique_text_values(
            list(
                freshness_blockers
            )
            +
            insight_blockers
        )
    )

    return {

        "status":
            freshness.get(
                "status"
            ),

        "reference_data_through":
            freshness.get(
                "reference_data_through"
            ),

        "blocking_datasets":
            blocking_datasets,

        "mixed_period_warning":
            bool(
                freshness.get(
                    "mixed_period_warning",
                    False,
                )
            ),

        "blocked_insight_count":
            len(
                blocked_insights
            ),

        "blocked_risk_count":
            len(
                [
                    insight
                    for insight
                    in blocked_insights
                    if insight.get(
                        "type"
                    )
                    ==
                    "risk"
                ]
            ),

        "blocked_opportunity_count":
            len(
                [
                    insight
                    for insight
                    in blocked_insights
                    if insight.get(
                        "type"
                    )
                    ==
                    "opportunity"
                ]
            ),
    }


# ============================================================
# READ-ONLY DASHBOARD SUMMARY
# ============================================================

def get_dashboard_summary() -> dict:

    # --------------------------------------------------------
    # Raw source freshness.
    #
    # data_through describes the latest sales row available.
    # It is deliberately different from analytical period end.
    # --------------------------------------------------------

    latest_date = (
        get_latest_sales_date()
    )

    # --------------------------------------------------------
    # Authoritative completed analytical periods.
    #
    # This is the same resolver used by Decision Intelligence.
    # The dashboard must not independently treat a partial new
    # month as a completed management cycle.
    # --------------------------------------------------------

    (
        current_period,
        comparison_period,
    ) = (
        latest_complete_periods()
    )

    current_start = (
        current_period.start
    )

    current_end = (
        current_period.end
    )

    comparison_start = (
        comparison_period.start
    )

    comparison_end = (
        comparison_period.end
    )

    current = (
        aggregate_period(
            current_start,
            current_end,
        )
    )

    previous = (
        aggregate_period(
            comparison_start,
            comparison_end,
        )
    )

    # --------------------------------------------------------
    # Evidence freshness is evaluated against exactly the same
    # completed period shown to management.
    # --------------------------------------------------------

    freshness = (
        get_data_freshness_report(
            reference_date=
                current_end
        )
    )

    # --------------------------------------------------------
    # Target analysis remains read-only.
    # --------------------------------------------------------

    target_payload = (
        analyze_targets(
            month_start=
                current_start
        )
    )

    # --------------------------------------------------------
    # Dashboard reads persisted intelligence only.
    #
    # No detection.
    # No lifecycle mutation.
    # --------------------------------------------------------

    active_insights = (
        get_active_insights()
    )

    all_risks = [
        item
        for item
        in active_insights
        if item.get(
            "type"
        )
        ==
        "risk"
    ]

    all_opportunities = [
        item
        for item
        in active_insights
        if item.get(
            "type"
        )
        ==
        "opportunity"
    ]

    current_risks = [
        item
        for item
        in all_risks
        if item.get(
            "resolution_blocked"
        )
        is not True
    ]

    blocked_risks = [
        item
        for item
        in all_risks
        if item.get(
            "resolution_blocked"
        )
        is True
    ]

    current_opportunities = [
        item
        for item
        in all_opportunities
        if item.get(
            "resolution_blocked"
        )
        is not True
    ]

    blocked_opportunities = [
        item
        for item
        in all_opportunities
        if item.get(
            "resolution_blocked"
        )
        is True
    ]

    brief = (
        build_business_brief(
            active_insights
        )
    )

    evidence = (
        build_evidence_summary(
            freshness=
                freshness,

            active_insights=
                active_insights,
        )
    )

    return {

        "data_through":
            latest_date,

        "current_period": {
            "start":
                current_start,

            "end":
                current_end,
        },

        "comparison_period": {
            "start":
                comparison_start,

            "end":
                comparison_end,
        },

        "evidence":
            evidence,

        "kpis": {

            "net_sales":
                comparison_kpi(
                    label=
                        "Net sales",

                    current=
                        current[
                            "net_sales"
                        ],

                    previous=
                        previous[
                            "net_sales"
                        ],

                    unit=
                        "value",
                ),

            "gross_profit":
                comparison_kpi(
                    label=
                        "Gross profit",

                    current=
                        current[
                            "gross_profit"
                        ],

                    previous=
                        previous[
                            "gross_profit"
                        ],

                    unit=
                        "value",
                ),

            "margin_pct":
                comparison_kpi(
                    label=
                        "Gross margin",

                    current=
                        current[
                            "margin_pct"
                        ],

                    previous=
                        previous[
                            "margin_pct"
                        ],

                    unit=
                        "percent",

                    use_percentage_points=
                        True,
                ),

            "units_sold":
                comparison_kpi(
                    label=
                        "Units sold",

                    current=
                        current[
                            "units_sold"
                        ],

                    previous=
                        previous[
                            "units_sold"
                        ],

                    unit=
                        "count",
                ),

            "target_attainment":
                build_target_summary(
                    target_payload
                ),
        },

        "brief":
            brief,

        "priorities": {

            "risk_count":
                len(
                    current_risks
                ),

            "active_risk_count":
                len(
                    all_risks
                ),

            "evidence_blocked_risk_count":
                len(
                    blocked_risks
                ),

            "opportunity_count":
                len(
                    current_opportunities
                ),

            "active_opportunity_count":
                len(
                    all_opportunities
                ),

            "evidence_blocked_opportunity_count":
                len(
                    blocked_opportunities
                ),

            # Overview shows only genuinely current signals.
            # Evidence-held prior issues remain visible in the
            # Priority Center rather than being presented as a
            # new current-period management signal.
            "risks":
                current_risks[
                    :3
                ],

            "opportunities":
                current_opportunities[
                    :2
                ],
        },

        "trend":
            monthly_trend(
                current_start
            ),

        "regions":
            region_performance(
                current_start=
                    current_start,

                current_end=
                    current_end,

                comparison_start=
                    comparison_start,

                comparison_end=
                    comparison_end,

                target_payload=
                    target_payload,
            ),
    }