from __future__ import annotations

from sqlalchemy import text

from ..database import engine

from .insight_service import (
    get_insight,
)

from .recommendation_service import (
    recommendation_actions,
)

from .scope import (
    BREAKDOWN_EXPRESSIONS,
    default_breakdowns,
    scope_filter,
)


# ============================================================
# HELPERS
# ============================================================

def as_float(
    value,
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
    current: float,
    previous: float,
) -> float | None:

    if previous == 0:

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


# ============================================================
# BREAKDOWN QUERY
# ============================================================

def breakdown(
    insight: dict,
    breakdown_dimension: str,
    limit: int = 8,
) -> list[dict]:

    expression = (
        BREAKDOWN_EXPRESSIONS.get(
            breakdown_dimension
        )
    )


    if expression is None:

        raise ValueError(
            (
                "Unsupported breakdown dimension: "
                f"{breakdown_dimension}"
            )
        )


    (
        filter_sql,
        filter_parameters,
    ) = (
        scope_filter(
            dimension=
                insight[
                    "dimension"
                ],

            value=
                insight[
                    "entity"
                ],
        )
    )


    query = text(
        f"""
        SELECT
            {expression} AS entity,

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
                            :previous_start
                            AND
                            :previous_end
                    THEN
                        f.net_sales
                    ELSE
                        0
                END
            ) AS previous_sales,

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
                        -
                        f.cogs
                    ELSE
                        0
                END
            ) AS current_gross_profit,

            SUM(
                CASE
                    WHEN
                        f.date_id
                        BETWEEN
                            :previous_start
                            AND
                            :previous_end
                    THEN
                        f.net_sales
                        -
                        f.cogs
                    ELSE
                        0
                END
            ) AS previous_gross_profit,

            SUM(
                CASE
                    WHEN
                        f.date_id
                        BETWEEN
                            :current_start
                            AND
                            :current_end
                    THEN
                        f.units_sold
                    ELSE
                        0
                END
            ) AS current_units,

            SUM(
                CASE
                    WHEN
                        f.date_id
                        BETWEEN
                            :previous_start
                            AND
                            :previous_end
                    THEN
                        f.units_sold
                    ELSE
                        0
                END
            ) AS previous_units

        FROM
            analytics.fact_sales_daily AS f

        INNER JOIN
            analytics.dim_store AS s
            ON
                s.store_id
                =
                f.store_id

        INNER JOIN
            analytics.dim_product AS p
            ON
                p.product_id
                =
                f.product_id

        LEFT JOIN
            analytics.dim_salesperson AS sp
            ON
                sp.salesperson_id
                =
                f.salesperson_id

        WHERE
            (
                f.date_id
                BETWEEN
                    :previous_start
                    AND
                    :current_end
            )

            AND
                {filter_sql}

        GROUP BY
            {expression}

        HAVING
            ABS(
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
                )
                -
                SUM(
                    CASE
                        WHEN
                            f.date_id
                            BETWEEN
                                :previous_start
                                AND
                                :previous_end
                        THEN
                            f.net_sales
                        ELSE
                            0
                    END
                )
            )
            >
            0

        ORDER BY
            ABS(
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
                )
                -
                SUM(
                    CASE
                        WHEN
                            f.date_id
                            BETWEEN
                                :previous_start
                                AND
                                :previous_end
                        THEN
                            f.net_sales
                        ELSE
                            0
                    END
                )
            )
            DESC

        LIMIT
            :limit;
        """
    )


    parameters = {

        "current_start":
            insight[
                "period_start"
            ],

        "current_end":
            insight[
                "period_end"
            ],

        "previous_start":
            insight[
                "comparison_start"
            ],

        "previous_end":
            insight[
                "comparison_end"
            ],

        "limit":
            limit,

        **filter_parameters,
    }


    with engine.connect() as connection:

        rows = (
            connection.execute(
                query,
                parameters,
            )
            .mappings()
            .all()
        )


    result = []


    for row in rows:

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


        current_gp = (
            as_float(
                row[
                    "current_gross_profit"
                ]
            )
            or
            0.0
        )


        previous_gp = (
            as_float(
                row[
                    "previous_gross_profit"
                ]
            )
            or
            0.0
        )


        current_margin = (
            (
                current_gp
                /
                current_sales
            )
            *
            100.0
            if current_sales
            else
            None
        )


        previous_margin = (
            (
                previous_gp
                /
                previous_sales
            )
            *
            100.0
            if previous_sales
            else
            None
        )


        margin_change_pp = (
            (
                current_margin
                -
                previous_margin
            )
            if (
                current_margin
                is not None
                and
                previous_margin
                is not None
            )
            else
            None
        )


        current_units = (
            as_float(
                row[
                    "current_units"
                ]
            )
            or
            0.0
        )


        previous_units = (
            as_float(
                row[
                    "previous_units"
                ]
            )
            or
            0.0
        )


        result.append(
            {
                "entity":
                    str(
                        row[
                            "entity"
                        ]
                    ),

                "current_sales":
                    round(
                        current_sales,
                        2,
                    ),

                "previous_sales":
                    round(
                        previous_sales,
                        2,
                    ),

                "sales_change":
                    round(
                        current_sales
                        -
                        previous_sales,
                        2,
                    ),

                "sales_change_pct":
                    percent_change(
                        current_sales,
                        previous_sales,
                    ),

                "gross_profit_change":
                    round(
                        current_gp
                        -
                        previous_gp,
                        2,
                    ),

                "margin_change_pp":
                    (
                        round(
                            margin_change_pp,
                            2,
                        )
                        if margin_change_pp
                        is not None
                        else
                        None
                    ),

                "units_change_pct":
                    percent_change(
                        current_units,
                        previous_units,
                    ),
            }
        )


    return result


# ============================================================
# INVESTIGATION
# ============================================================

def investigate_insight(
    insight_id: int,
) -> dict:

    insight = (
        get_insight(
            insight_id
        )
    )


    breakdown_dimensions = (
        default_breakdowns(
            insight[
                "dimension"
            ]
        )
    )


    breakdowns = {}


    for dimension in (
        breakdown_dimensions
    ):

        breakdowns[
            dimension
        ] = (
            breakdown(
                insight=
                    insight,

                breakdown_dimension=
                    dimension,
            )
        )


    recommendations = (
        recommendation_actions(
            diagnosis=
                insight.get(
                    "diagnosis"
                ),

            entity=
                insight[
                    "entity"
                ],
        )
    )


    return {

        "insight":
            insight,

        "period": {

            "current_start":
                insight[
                    "period_start"
                ],

            "current_end":
                insight[
                    "period_end"
                ],

            "comparison_start":
                insight[
                    "comparison_start"
                ],

            "comparison_end":
                insight[
                    "comparison_end"
                ],
        },

        "breakdowns":
            breakdowns,

        "recommendations":
            recommendations,
    }