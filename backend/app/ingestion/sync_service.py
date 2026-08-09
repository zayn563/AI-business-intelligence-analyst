import io

import psycopg

from ..config import settings


# ============================================================
# DATABASE CONFIGURATION
# ============================================================

DB_CONFIG = {

    "host":
        settings.db_host,

    "port":
        settings.db_port,

    "dbname":
        settings.db_name,

    "user":
        settings.db_user,

    "password":
        settings.db_password,
}


# ============================================================
# STAGING COLUMNS
# ============================================================

STAGING_COLUMNS = [

    "date_id",

    "store_id",

    "product_id",

    "salesperson_id",

    "units_sold",

    "transactions",

    "gross_sales",

    "discount_amount",

    "net_sales",

    "cogs",

    "returns_value",

    "promo_flag",

    "source_record_key",

    "source_record_hash",
]


# ============================================================
# TEMPORARY STAGING TABLE
# ============================================================

CREATE_TEMP_TABLE_SQL = """
CREATE TEMP TABLE temp_sales_refresh (

    date_id DATE NOT NULL,

    store_id INTEGER NOT NULL,

    product_id INTEGER NOT NULL,

    salesperson_id INTEGER NOT NULL,

    units_sold INTEGER NOT NULL,

    transactions INTEGER NOT NULL,

    gross_sales NUMERIC(14,2) NOT NULL,

    discount_amount NUMERIC(14,2) NOT NULL,

    net_sales NUMERIC(14,2) NOT NULL,

    cogs NUMERIC(14,2) NOT NULL,

    returns_value NUMERIC(14,2) NOT NULL,

    promo_flag BOOLEAN NOT NULL,

    source_record_key TEXT NOT NULL,

    source_record_hash VARCHAR(64) NOT NULL

) ON COMMIT DROP;
"""


# ============================================================
# COPY DATAFRAME INTO TEMP TABLE
# ============================================================

def _copy_dataframe(
    cursor,
    dataframe,
):

    buffer = io.StringIO()


    dataframe[
        STAGING_COLUMNS
    ].to_csv(
        buffer,
        index=False,
        header=False,
        na_rep="",
    )


    buffer.seek(
        0
    )


    copy_sql = """
        COPY temp_sales_refresh (
            date_id,
            store_id,
            product_id,
            salesperson_id,
            units_sold,
            transactions,
            gross_sales,
            discount_amount,
            net_sales,
            cogs,
            returns_value,
            promo_flag,
            source_record_key,
            source_record_hash
        )
        FROM STDIN
        WITH (
            FORMAT CSV,
            NULL ''
        );
    """


    with cursor.copy(
        copy_sql
    ) as copy:

        while True:

            chunk = buffer.read(
                1024 * 1024
            )


            if not chunk:
                break


            copy.write(
                chunk
            )


# ============================================================
# DIMENSION KEY VALIDATION
# ============================================================

def _validate_dimension_keys(
    cursor,
):

    checks = [

        (
            "store_id",
            "analytics.dim_store",
            "store_id",
        ),

        (
            "product_id",
            "analytics.dim_product",
            "product_id",
        ),

        (
            "salesperson_id",
            "analytics.dim_salesperson",
            "salesperson_id",
        ),
    ]


    for (
        field,
        dimension_table,
        dimension_field,
    ) in checks:

        cursor.execute(
            f"""
            SELECT COUNT(DISTINCT t.{field})

            FROM temp_sales_refresh t

            LEFT JOIN {dimension_table} d
                ON
                    t.{field}
                    =
                    d.{dimension_field}

            WHERE
                d.{dimension_field}
                IS NULL;
            """
        )


        missing_count = (
            cursor.fetchone()[0]
        )


        if missing_count > 0:

            cursor.execute(
                f"""
                SELECT DISTINCT
                    t.{field}

                FROM temp_sales_refresh t

                LEFT JOIN {dimension_table} d
                    ON
                        t.{field}
                        =
                        d.{dimension_field}

                WHERE
                    d.{dimension_field}
                    IS NULL

                LIMIT 10;
                """
            )


            samples = [

                row[0]

                for row
                in cursor.fetchall()
            ]


            raise ValueError(
                f"Source contains "
                f"{missing_count} unknown "
                f"{field} values. "
                f"Examples: {samples}"
            )


# ============================================================
# INSERTED COUNT
# ============================================================

def _count_inserted(
    cursor,
) -> int:

    cursor.execute(
        """
        SELECT COUNT(*)

        FROM temp_sales_refresh t

        LEFT JOIN analytics.fact_sales_daily f

            ON
                f.date_id =
                    t.date_id

                AND f.store_id =
                    t.store_id

                AND f.product_id =
                    t.product_id

        WHERE
            f.sales_id IS NULL;
        """
    )


    return int(
        cursor.fetchone()[0]
    )


# ============================================================
# UPDATED COUNT
# ============================================================

def _count_updated(
    cursor,
) -> int:

    cursor.execute(
        """
        SELECT COUNT(*)

        FROM temp_sales_refresh t

        JOIN analytics.fact_sales_daily f

            ON
                f.date_id =
                    t.date_id

                AND f.store_id =
                    t.store_id

                AND f.product_id =
                    t.product_id

        WHERE

            ROW(
                f.salesperson_id,
                f.units_sold,
                f.transactions,
                f.gross_sales,
                f.discount_amount,
                f.net_sales,
                f.cogs,
                f.returns_value,
                f.promo_flag
            )

            IS DISTINCT FROM

            ROW(
                t.salesperson_id,
                t.units_sold,
                t.transactions,
                t.gross_sales,
                t.discount_amount,
                t.net_sales,
                t.cogs,
                t.returns_value,
                t.promo_flag
            );
        """
    )


    return int(
        cursor.fetchone()[0]
    )


# ============================================================
# UPSERT
# ============================================================

UPSERT_SQL = """
INSERT INTO analytics.fact_sales_daily AS f (

    date_id,

    store_id,

    product_id,

    salesperson_id,

    units_sold,

    transactions,

    gross_sales,

    discount_amount,

    net_sales,

    cogs,

    returns_value,

    promo_flag
)

SELECT

    date_id,

    store_id,

    product_id,

    salesperson_id,

    units_sold,

    transactions,

    gross_sales,

    discount_amount,

    net_sales,

    cogs,

    returns_value,

    promo_flag

FROM temp_sales_refresh

ON CONFLICT (
    date_id,
    store_id,
    product_id
)

DO UPDATE

SET
    salesperson_id =
        EXCLUDED.salesperson_id,

    units_sold =
        EXCLUDED.units_sold,

    transactions =
        EXCLUDED.transactions,

    gross_sales =
        EXCLUDED.gross_sales,

    discount_amount =
        EXCLUDED.discount_amount,

    net_sales =
        EXCLUDED.net_sales,

    cogs =
        EXCLUDED.cogs,

    returns_value =
        EXCLUDED.returns_value,

    promo_flag =
        EXCLUDED.promo_flag

WHERE

    ROW(
        f.salesperson_id,
        f.units_sold,
        f.transactions,
        f.gross_sales,
        f.discount_amount,
        f.net_sales,
        f.cogs,
        f.returns_value,
        f.promo_flag
    )

    IS DISTINCT FROM

    ROW(
        EXCLUDED.salesperson_id,
        EXCLUDED.units_sold,
        EXCLUDED.transactions,
        EXCLUDED.gross_sales,
        EXCLUDED.discount_amount,
        EXCLUDED.net_sales,
        EXCLUDED.cogs,
        EXCLUDED.returns_value,
        EXCLUDED.promo_flag
    );
"""


# ============================================================
# APPEND-ONLY
# ============================================================

APPEND_SQL = """
INSERT INTO analytics.fact_sales_daily (

    date_id,

    store_id,

    product_id,

    salesperson_id,

    units_sold,

    transactions,

    gross_sales,

    discount_amount,

    net_sales,

    cogs,

    returns_value,

    promo_flag
)

SELECT

    date_id,

    store_id,

    product_id,

    salesperson_id,

    units_sold,

    transactions,

    gross_sales,

    discount_amount,

    net_sales,

    cogs,

    returns_value,

    promo_flag

FROM temp_sales_refresh

ON CONFLICT (
    date_id,
    store_id,
    product_id
)

DO NOTHING;
"""


# ============================================================
# UPDATE SOURCE RECORD STATE
# ============================================================

SOURCE_STATE_SQL = """
INSERT INTO analytics.source_record_state (

    source_id,

    source_record_key,

    record_hash,

    first_seen_at,

    last_seen_at
)

SELECT

    %s,

    source_record_key,

    source_record_hash,

    NOW(),

    NOW()

FROM temp_sales_refresh

ON CONFLICT (
    source_id,
    source_record_key
)

DO UPDATE

SET
    record_hash =
        EXCLUDED.record_hash,

    last_seen_at =
        NOW();
"""


# ============================================================
# MAIN SYNC
# ============================================================

def sync_sales_fact(
    dataframe,
    source_id: int,
    load_strategy: str = "upsert",
) -> dict:

    rows_read = len(
        dataframe
    )


    with psycopg.connect(
        **DB_CONFIG
    ) as connection:

        with connection.cursor() as cursor:

            cursor.execute(
                CREATE_TEMP_TABLE_SQL
            )


            _copy_dataframe(
                cursor,
                dataframe,
            )


            _validate_dimension_keys(
                cursor
            )


            inserted = (
                _count_inserted(
                    cursor
                )
            )


            if load_strategy == "upsert":

                updated = (
                    _count_updated(
                        cursor
                    )
                )

                cursor.execute(
                    UPSERT_SQL
                )


            elif load_strategy == "append":

                updated = 0

                cursor.execute(
                    APPEND_SQL
                )


            else:

                raise ValueError(
                    f"Unsupported load strategy: "
                    f"{load_strategy}"
                )


            unchanged = (

                rows_read
                - inserted
                - updated
            )


            cursor.execute(
                SOURCE_STATE_SQL,
                (
                    source_id,
                ),
            )


    return {

        "rows_read":
            rows_read,

        "rows_inserted":
            inserted,

        "rows_updated":
            updated,

        "rows_unchanged":
            unchanged,

        "rows_rejected":
            0,
    }