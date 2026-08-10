from datetime import date

from sqlalchemy import text

from ..database import engine


# ============================================================
# SAFE DIMENSION WHITELIST
# ============================================================

DIMENSION_EXPRESSIONS = {

    "overall":
        "'Overall'",

    "region":
        "s.region",

    "city":
        "s.city",

    "channel":
        "s.channel",

    "category":
        "p.category",

    "brand":
        "p.brand",

    "product":
        (
            "CAST(p.product_id AS TEXT)"
            " || ' | ' || "
            "p.product_name"
        ),

    "store":
        (
            "CAST(s.store_id AS TEXT)"
            " || ' | ' || "
            "s.store_name"
        ),

    "salesperson":
        (
            "CAST(sp.salesperson_id AS TEXT)"
            " || ' | ' || "
            "sp.salesperson_name"
        ),
}


INVENTORY_SUPPORTED_DIMENSIONS = {
    "overall",
    "region",
    "city",
    "channel",
    "category",
    "brand",
    "product",
    "store",
}


# ============================================================
# DATA COVERAGE
# ============================================================

def get_max_sales_date() -> date:

    query = text(
        """
        SELECT
            MAX(date_id)
        FROM
            analytics.fact_sales_daily;
        """
    )

    with engine.connect() as connection:

        value = (
            connection
            .execute(query)
            .scalar_one()
        )

    if value is None:

        raise ValueError(
            "Sales fact table contains no data."
        )

    return value


# ============================================================
# SALES SNAPSHOT
# ============================================================

def fetch_sales_snapshot(
    start_date: date,
    end_date: date,
    dimension: str,
) -> dict[str, dict]:

    if (
        dimension
        not in DIMENSION_EXPRESSIONS
    ):

        raise ValueError(
            f"Unsupported dimension: {dimension}"
        )

    expression = (
        DIMENSION_EXPRESSIONS[
            dimension
        ]
    )

    if dimension == "overall":

        group_by = ""

    else:

        group_by = (
            f"GROUP BY {expression}"
        )

    sql = f"""
        SELECT
            {expression}
                AS dimension_value,

            CAST(
                SUM(f.net_sales)
                AS DOUBLE PRECISION
            )
                AS net_sales,

            CAST(
                SUM(f.units_sold)
                AS DOUBLE PRECISION
            )
                AS units_sold,

            CAST(
                SUM(f.transactions)
                AS DOUBLE PRECISION
            )
                AS transactions,

            CAST(
                SUM(
                    f.net_sales
                    -
                    f.cogs
                )
                AS DOUBLE PRECISION
            )
                AS gross_profit,

            CAST(
                100.0
                *
                SUM(
                    f.net_sales
                    -
                    f.cogs
                )
                /
                NULLIF(
                    SUM(f.net_sales),
                    0
                )
                AS DOUBLE PRECISION
            )
                AS margin_pct,

            CAST(
                SUM(f.net_sales)
                /
                NULLIF(
                    SUM(f.units_sold),
                    0
                )
                AS DOUBLE PRECISION
            )
                AS avg_selling_price,

            CAST(
                100.0
                *
                SUM(f.discount_amount)
                /
                NULLIF(
                    SUM(f.gross_sales),
                    0
                )
                AS DOUBLE PRECISION
            )
                AS discount_pct,

            CAST(
                SUM(f.cogs)
                /
                NULLIF(
                    SUM(f.units_sold),
                    0
                )
                AS DOUBLE PRECISION
            )
                AS cost_per_unit

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

        JOIN
            analytics.dim_salesperson sp
            ON
            f.salesperson_id
            =
            sp.salesperson_id

        WHERE
            f.date_id
            BETWEEN
            :start_date
            AND
            :end_date

        {group_by}

        ORDER BY
            1;
    """

    query = text(sql)

    with engine.connect() as connection:

        rows = (
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
            .all()
        )

    result = {}

    for row in rows:

        key = str(
            row[
                "dimension_value"
            ]
        )

        result[key] = {
            "dimension_value":
                key,

            "net_sales":
                row["net_sales"],

            "units_sold":
                row["units_sold"],

            "transactions":
                row["transactions"],

            "gross_profit":
                row["gross_profit"],

            "margin_pct":
                row["margin_pct"],

            "avg_selling_price":
                row[
                    "avg_selling_price"
                ],

            "discount_pct":
                row["discount_pct"],

            "cost_per_unit":
                row["cost_per_unit"],
        }

    return result


# ============================================================
# INVENTORY SNAPSHOT
# ============================================================

def fetch_inventory_snapshot(
    start_date: date,
    end_date: date,
    dimension: str,
) -> dict[str, dict]:

    if (
        dimension
        not in
        INVENTORY_SUPPORTED_DIMENSIONS
    ):

        return {}

    expression = (
        DIMENSION_EXPRESSIONS[
            dimension
        ]
    )

    if dimension == "overall":

        group_by = ""

    else:

        group_by = (
            f"GROUP BY {expression}"
        )

    sql = f"""
        SELECT
            {expression}
                AS dimension_value,

            CAST(
                100.0
                *
                COUNT(*)
                    FILTER (
                        WHERE
                            i.stockout_flag
                            =
                            TRUE
                    )
                /
                NULLIF(
                    COUNT(*),
                    0
                )
                AS DOUBLE PRECISION
            )
                AS stockout_rate

        FROM
            analytics.fact_inventory_daily i

        JOIN
            analytics.dim_store s
            ON
            i.store_id
            =
            s.store_id

        JOIN
            analytics.dim_product p
            ON
            i.product_id
            =
            p.product_id

        WHERE
            i.date_id
            BETWEEN
            :start_date
            AND
            :end_date

        {group_by}

        ORDER BY
            1;
    """

    query = text(sql)

    with engine.connect() as connection:

        rows = (
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
            .all()
        )

    return {
        str(
            row[
                "dimension_value"
            ]
        ): {
            "stockout_rate":
                row[
                    "stockout_rate"
                ]
        }
        for row
        in rows
    }


# ============================================================
# COMBINED KPI SNAPSHOT
# ============================================================

def get_kpi_snapshot(
    start_date: date,
    end_date: date,
    dimension: str,
) -> dict[str, dict]:

    sales = (
        fetch_sales_snapshot(
            start_date,
            end_date,
            dimension,
        )
    )

    inventory = (
        fetch_inventory_snapshot(
            start_date,
            end_date,
            dimension,
        )
    )

    result = {}

    for key, sales_row in (
        sales.items()
    ):

        row = dict(
            sales_row
        )

        inventory_row = (
            inventory.get(
                key,
                {},
            )
        )

        row[
            "stockout_rate"
        ] = (
            inventory_row.get(
                "stockout_rate"
            )
        )

        result[key] = row

    return result