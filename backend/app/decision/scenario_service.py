from __future__ import annotations

from datetime import date

from sqlalchemy import text

from ..database import engine

from .insight_service import (
    get_insight,
)

from .models import (
    ScenarioRequest,
)

from .scope import (
    scope_filter,
)


# ============================================================
# HELPERS
# ============================================================

def as_float(
    value,
) -> float:

    if value is None:
        return 0.0

    return float(
        value
    )


# ============================================================
# LATEST DATE
# ============================================================

def latest_sales_date() -> date:

    with engine.connect() as connection:

        value = (
            connection.execute(
                text(
                    """
                    SELECT
                        MAX(date_id)
                    FROM
                        analytics.fact_sales_daily;
                    """
                )
            )
            .scalar_one()
        )


    if value is None:

        raise ValueError(
            "No sales data is available."
        )


    return value


# ============================================================
# BASELINE
# ============================================================

def baseline_for_scope(
    dimension: str,
    value: str,
    start_date: date,
    end_date: date,
) -> dict:

    (
        filter_sql,
        filter_parameters,
    ) = (
        scope_filter(
            dimension=
                dimension,

            value=
                value,
        )
    )


    query = text(
        f"""
        SELECT
            SUM(
                f.net_sales
            ) AS net_sales,

            SUM(
                f.units_sold
            ) AS units_sold,

            SUM(
                f.cogs
            ) AS cogs,

            SUM(
                f.discount_amount
            ) AS discount_amount

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
            f.date_id
            BETWEEN
                :start_date
                AND
                :end_date

            AND
                {filter_sql};
        """
    )


    with engine.connect() as connection:

        row = (
            connection.execute(
                query,
                {
                    "start_date":
                        start_date,

                    "end_date":
                        end_date,

                    **filter_parameters,
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
    )


    units = (
        as_float(
            row[
                "units_sold"
            ]
        )
    )


    cogs = (
        as_float(
            row[
                "cogs"
            ]
        )
    )


    discount = (
        as_float(
            row[
                "discount_amount"
            ]
        )
    )


    gross_revenue = (
        net_sales
        +
        discount
    )


    list_price_per_unit = (
        gross_revenue
        /
        units
        if units
        else
        0.0
    )


    cost_per_unit = (
        cogs
        /
        units
        if units
        else
        0.0
    )


    discount_rate = (
        discount
        /
        gross_revenue
        if gross_revenue
        else
        0.0
    )


    gross_profit = (
        net_sales
        -
        cogs
    )


    margin_pct = (
        gross_profit
        /
        net_sales
        *
        100.0
        if net_sales
        else
        0.0
    )


    return {

        "net_sales":
            net_sales,

        "units_sold":
            units,

        "cogs":
            cogs,

        "gross_profit":
            gross_profit,

        "margin_pct":
            margin_pct,

        "discount_rate":
            discount_rate,

        "list_price_per_unit":
            list_price_per_unit,

        "cost_per_unit":
            cost_per_unit,
    }


# ============================================================
# SCENARIO
# ============================================================

def run_scenario(
    request: ScenarioRequest,
) -> dict:

    if request.insight_id is not None:

        insight = (
            get_insight(
                request.insight_id
            )
        )


        dimension = (
            insight[
                "dimension"
            ]
        )


        value = (
            insight[
                "entity"
            ]
        )


        start_date = (
            insight[
                "period_start"
            ]
        )


        end_date = (
            insight[
                "period_end"
            ]
        )


    else:

        latest = (
            latest_sales_date()
        )


        dimension = (
            "overall"
        )


        value = (
            "Overall"
        )


        start_date = date(
            latest.year,
            latest.month,
            1,
        )


        end_date = (
            latest
        )


    baseline = (
        baseline_for_scope(
            dimension=
                dimension,

            value=
                value,

            start_date=
                start_date,

            end_date=
                end_date,
        )
    )


    scenario_units = (
        baseline[
            "units_sold"
        ]
        *
        (
            1.0
            +
            request.volume_change_pct
            /
            100.0
        )
    )


    scenario_list_price = (
        baseline[
            "list_price_per_unit"
        ]
        *
        (
            1.0
            +
            request.list_price_change_pct
            /
            100.0
        )
    )


    scenario_discount_rate = (
        baseline[
            "discount_rate"
        ]
        +
        request.discount_rate_change_pp
        /
        100.0
    )


    scenario_discount_rate = max(
        0.0,
        min(
            scenario_discount_rate,
            0.95,
        ),
    )


    scenario_cost_per_unit = (
        baseline[
            "cost_per_unit"
        ]
        *
        (
            1.0
            +
            request.cost_per_unit_change_pct
            /
            100.0
        )
    )


    scenario_gross_revenue = (
        scenario_units
        *
        scenario_list_price
    )


    scenario_net_sales = (
        scenario_gross_revenue
        *
        (
            1.0
            -
            scenario_discount_rate
        )
    )


    scenario_cogs = (
        scenario_units
        *
        scenario_cost_per_unit
    )


    scenario_gross_profit = (
        scenario_net_sales
        -
        scenario_cogs
    )


    scenario_margin = (
        (
            scenario_gross_profit
            /
            scenario_net_sales
        )
        *
        100.0
        if scenario_net_sales
        else
        0.0
    )


    return {

        "scope": {

            "dimension":
                dimension,

            "value":
                value,

            "start_date":
                start_date,

            "end_date":
                end_date,
        },


        "levers": {

            "volume_change_pct":
                request.volume_change_pct,

            "list_price_change_pct":
                request.list_price_change_pct,

            "discount_rate_change_pp":
                request.discount_rate_change_pp,

            "cost_per_unit_change_pct":
                request.cost_per_unit_change_pct,
        },


        "baseline": {

            "net_sales":
                round(
                    baseline[
                        "net_sales"
                    ],
                    2,
                ),

            "gross_profit":
                round(
                    baseline[
                        "gross_profit"
                    ],
                    2,
                ),

            "margin_pct":
                round(
                    baseline[
                        "margin_pct"
                    ],
                    2,
                ),

            "units_sold":
                round(
                    baseline[
                        "units_sold"
                    ],
                    2,
                ),

            "discount_rate_pct":
                round(
                    baseline[
                        "discount_rate"
                    ]
                    *
                    100.0,
                    2,
                ),

            "cost_per_unit":
                round(
                    baseline[
                        "cost_per_unit"
                    ],
                    4,
                ),
        },


        "scenario": {

            "net_sales":
                round(
                    scenario_net_sales,
                    2,
                ),

            "gross_profit":
                round(
                    scenario_gross_profit,
                    2,
                ),

            "margin_pct":
                round(
                    scenario_margin,
                    2,
                ),

            "units_sold":
                round(
                    scenario_units,
                    2,
                ),

            "discount_rate_pct":
                round(
                    scenario_discount_rate
                    *
                    100.0,
                    2,
                ),

            "cost_per_unit":
                round(
                    scenario_cost_per_unit,
                    4,
                ),
        },


        "impact": {

            "net_sales_change":
                round(
                    scenario_net_sales
                    -
                    baseline[
                        "net_sales"
                    ],
                    2,
                ),

            "gross_profit_change":
                round(
                    scenario_gross_profit
                    -
                    baseline[
                        "gross_profit"
                    ],
                    2,
                ),

            "margin_change_pp":
                round(
                    scenario_margin
                    -
                    baseline[
                        "margin_pct"
                    ],
                    2,
                ),
        },
    }