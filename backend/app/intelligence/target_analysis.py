from calendar import monthrange
from datetime import date

from sqlalchemy import text

from ..database import engine


# ============================================================
# TARGET STATUS RULES
# ============================================================

def classify_target_achievement(
    achievement_pct: float | None,
) -> dict:

    if achievement_pct is None:
        return {
            "status": "not_available",
            "severity": "informational",
            "material": False,
            "impact": "neutral",
        }

    if achievement_pct >= 100:
        return {
            "status": "achieved",
            "severity": "informational",
            "material": False,
            "impact": "positive",
        }

    if achievement_pct >= 95:
        return {
            "status": "watch",
            "severity": "low",
            "material": True,
            "impact": "negative",
        }

    if achievement_pct >= 90:
        return {
            "status": "at_risk",
            "severity": "medium",
            "material": True,
            "impact": "negative",
        }

    return {
        "status": "missed",
        "severity": "high",
        "material": True,
        "impact": "negative",
    }


# ============================================================
# HELPERS
# ============================================================

def latest_target_month() -> date:

    query = text(
        """
        SELECT MAX(month_start)
        FROM analytics.fact_targets_monthly;
        """
    )

    with engine.connect() as connection:
        value = connection.execute(query).scalar_one()

    if value is None:
        raise ValueError(
            "No monthly targets are available."
        )

    return value


def month_end(
    month_start: date,
) -> date:

    return date(
        month_start.year,
        month_start.month,
        monthrange(
            month_start.year,
            month_start.month,
        )[1],
    )


def percentage(
    numerator: float,
    denominator: float,
) -> float | None:

    if denominator == 0:
        return None

    return (
        numerator
        /
        denominator
        *
        100.0
    )


def rounded(
    value,
    digits=2,
):

    if value is None:
        return None

    return round(
        float(value),
        digits,
    )


# ============================================================
# TARGET QUERY
# ============================================================

def fetch_target_rows(
    month_start: date,
) -> list[dict]:

    end_date = month_end(
        month_start
    )

    query = text(
        """
        WITH actuals AS (
            SELECT
                s.region,
                p.category,

                SUM(
                    f.net_sales
                )::double precision
                    AS actual_sales,

                SUM(
                    f.units_sold
                )::double precision
                    AS actual_units,

                (
                    100.0
                    *
                    SUM(
                        f.net_sales
                        -
                        f.cogs
                    )
                    /
                    NULLIF(
                        SUM(
                            f.net_sales
                        ),
                        0
                    )
                )::double precision
                    AS actual_margin_pct

            FROM
                analytics.fact_sales_daily f

            JOIN
                analytics.dim_store s
                ON
                f.store_id
                =
                s.store_id

            JOIN
                analytics.dim_product p
                ON
                f.product_id
                =
                p.product_id

            WHERE
                f.date_id
                BETWEEN
                :month_start
                AND
                :month_end

            GROUP BY
                s.region,
                p.category
        )

        SELECT
            t.month_start,
            t.region,
            t.category,

            t.sales_target::double precision
                AS sales_target,

            t.units_target::double precision
                AS units_target,

            t.margin_target_pct::double precision
                AS margin_target_pct,

            COALESCE(
                a.actual_sales,
                0
            )::double precision
                AS actual_sales,

            COALESCE(
                a.actual_units,
                0
            )::double precision
                AS actual_units,

            a.actual_margin_pct

        FROM
            analytics.fact_targets_monthly t

        LEFT JOIN
            actuals a
            ON
            t.region
            =
            a.region

            AND

            t.category
            =
            a.category

        WHERE
            t.month_start
            =
            :month_start

        ORDER BY
            t.region,
            t.category;
        """
    )

    with engine.connect() as connection:

        rows = (
            connection
            .execute(
                query,
                {
                    "month_start":
                        month_start,

                    "month_end":
                        end_date,
                },
            )
            .mappings()
            .all()
        )

    return [
        dict(row)
        for row in rows
    ]


# ============================================================
# TARGET ANALYSIS
# ============================================================

def analyze_targets(
    month_start: date | None = None,
) -> dict:

    if month_start is None:
        month_start = (
            latest_target_month()
        )

    rows = fetch_target_rows(
        month_start
    )

    category_results = []

    region_aggregation = {}

    for row in rows:

        actual_sales = float(
            row["actual_sales"]
        )

        sales_target = float(
            row["sales_target"]
        )

        actual_units = float(
            row["actual_units"]
        )

        units_target = float(
            row["units_target"]
        )

        sales_achievement = (
            percentage(
                actual_sales,
                sales_target,
            )
        )

        units_achievement = (
            percentage(
                actual_units,
                units_target,
            )
        )

        classification = (
            classify_target_achievement(
                sales_achievement
            )
        )

        result = {
            "month_start":
                month_start.isoformat(),

            "region":
                row["region"],

            "category":
                row["category"],

            "actual_sales":
                rounded(
                    actual_sales
                ),

            "sales_target":
                rounded(
                    sales_target
                ),

            "sales_gap":
                rounded(
                    actual_sales
                    -
                    sales_target
                ),

            "sales_achievement_pct":
                rounded(
                    sales_achievement
                ),

            "actual_units":
                rounded(
                    actual_units
                ),

            "units_target":
                rounded(
                    units_target
                ),

            "units_achievement_pct":
                rounded(
                    units_achievement
                ),

            "actual_margin_pct":
                rounded(
                    row[
                        "actual_margin_pct"
                    ]
                ),

            "margin_target_pct":
                rounded(
                    row[
                        "margin_target_pct"
                    ]
                ),

            **classification,
        }

        category_results.append(
            result
        )

        region = row["region"]

        if (
            region
            not in
            region_aggregation
        ):

            region_aggregation[
                region
            ] = {
                "actual_sales": 0.0,
                "sales_target": 0.0,
                "actual_units": 0.0,
                "units_target": 0.0,
            }

        bucket = (
            region_aggregation[
                region
            ]
        )

        bucket[
            "actual_sales"
        ] += actual_sales

        bucket[
            "sales_target"
        ] += sales_target

        bucket[
            "actual_units"
        ] += actual_units

        bucket[
            "units_target"
        ] += units_target


    region_results = []

    for region, values in (
        region_aggregation.items()
    ):

        sales_achievement = (
            percentage(
                values[
                    "actual_sales"
                ],
                values[
                    "sales_target"
                ],
            )
        )

        units_achievement = (
            percentage(
                values[
                    "actual_units"
                ],
                values[
                    "units_target"
                ],
            )
        )

        classification = (
            classify_target_achievement(
                sales_achievement
            )
        )

        region_results.append(
            {
                "region":
                    region,

                "actual_sales":
                    rounded(
                        values[
                            "actual_sales"
                        ]
                    ),

                "sales_target":
                    rounded(
                        values[
                            "sales_target"
                        ]
                    ),

                "sales_gap":
                    rounded(
                        values[
                            "actual_sales"
                        ]
                        -
                        values[
                            "sales_target"
                        ]
                    ),

                "sales_achievement_pct":
                    rounded(
                        sales_achievement
                    ),

                "actual_units":
                    rounded(
                        values[
                            "actual_units"
                        ]
                    ),

                "units_target":
                    rounded(
                        values[
                            "units_target"
                        ]
                    ),

                "units_achievement_pct":
                    rounded(
                        units_achievement
                    ),

                **classification,
            }
        )


    severity_order = {
        "high": 3,
        "medium": 2,
        "low": 1,
        "informational": 0,
    }

    region_results.sort(
        key=lambda row: (
            severity_order.get(
                row[
                    "severity"
                ],
                0,
            ),
            -(
                row.get(
                    "sales_achievement_pct"
                )
                or
                999
            ),
        ),
        reverse=True,
    )

    material_misses = [
        row
        for row
        in region_results
        if row[
            "material"
        ]
    ]

    return {
        "status":
            "success",

        "analysis_type":
            "target_achievement",

        "month_start":
            month_start.isoformat(),

        "region_summary":
            region_results,

        "category_detail":
            category_results,

        "material_target_issues":
            material_misses,

        "summary": {
            "regions_evaluated":
                len(
                    region_results
                ),

            "regions_on_target":
                sum(
                    1
                    for row
                    in region_results
                    if row[
                        "status"
                    ]
                    ==
                    "achieved"
                ),

            "regions_at_risk":
                len(
                    material_misses
                ),

            "high_priority_misses":
                sum(
                    1
                    for row
                    in material_misses
                    if row[
                        "severity"
                    ]
                    ==
                    "high"
                ),
        },
    }