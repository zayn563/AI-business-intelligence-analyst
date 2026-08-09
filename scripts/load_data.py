from pathlib import Path
import os
import sys
import time

import psycopg
from dotenv import load_dotenv


# ============================================================
# PROJECT PATHS
# ============================================================

ROOT = Path(__file__).resolve().parents[1]

ENV_FILE = ROOT / ".env"

DATA_DIR = (
    ROOT
    / "data"
    / "generated"
)


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv(
    dotenv_path=ENV_FILE,
    override=True
)


DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": int(os.getenv("DB_PORT", 5432)),
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
}


# ============================================================
# FILE / TABLE DEFINITIONS
#
# IMPORTANT:
# Dimensions load first.
# Facts load afterward because they depend on dimensions.
# ============================================================

TABLES = [

    # --------------------------------------------------------
    # DIMENSIONS
    # --------------------------------------------------------

    {
        "table": "analytics.dim_date",

        "file": "dim_date.csv",

        "columns": [
            "date_id",
            "year",
            "quarter",
            "month",
            "month_name",
            "week",
            "day_of_month",
            "day_of_week",
            "day_name",
            "is_weekend",
        ],
    },


    {
        "table": "analytics.dim_store",

        "file": "dim_store.csv",

        "columns": [
            "store_id",
            "store_name",
            "city",
            "region",
            "channel",
            "store_format",
            "latitude",
            "longitude",
            "opened_date",
        ],
    },


    {
        "table": "analytics.dim_product",

        "file": "dim_product.csv",

        "columns": [
            "product_id",
            "product_name",
            "brand",
            "category",
            "subcategory",
            "pack_size",
            "list_price",
            "standard_cost",
        ],
    },


    {
        "table": "analytics.dim_salesperson",

        "file": "dim_salesperson.csv",

        "columns": [
            "salesperson_id",
            "salesperson_name",
            "region",
            "team",
            "manager_name",
        ],
    },


    # --------------------------------------------------------
    # FACT TABLES
    # --------------------------------------------------------

    {
        "table": "analytics.fact_sales_daily",

        "file": "fact_sales_daily.csv",

        "columns": [
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
        ],
    },


    {
        "table": "analytics.fact_inventory_daily",

        "file": "fact_inventory_daily.csv",

        "columns": [
            "date_id",
            "store_id",
            "product_id",
            "opening_stock",
            "received_units",
            "closing_stock",
            "stockout_flag",
        ],
    },


    {
        "table": "analytics.fact_targets_monthly",

        "file": "fact_targets_monthly.csv",

        "columns": [
            "month_start",
            "region",
            "category",
            "sales_target",
            "units_target",
            "margin_target_pct",
        ],
    },


    {
        "table": "analytics.fact_promotions",

        "file": "fact_promotions.csv",

        "columns": [
            "promotion_id",
            "product_id",
            "region",
            "promotion_type",
            "campaign_name",
            "start_date",
            "end_date",
            "discount_pct",
        ],
    },
]


# ============================================================
# EXPECTED ROW COUNTS
#
# Fixed master dimensions can be validated exactly.
# Fact rows are checked after loading.
# ============================================================

EXPECTED_FIXED_COUNTS = {
    "analytics.dim_date": 577,
    "analytics.dim_store": 60,
    "analytics.dim_product": 20,
    "analytics.dim_salesperson": 10,
    "analytics.fact_promotions": 1,
}


# ============================================================
# VALIDATE REQUIRED FILES
# ============================================================

def validate_files():

    print("\nChecking generated data files...")

    missing_files = []

    for item in TABLES:

        file_path = (
            DATA_DIR
            / item["file"]
        )

        if not file_path.exists():

            missing_files.append(
                str(file_path)
            )

        else:

            size_mb = (
                file_path.stat().st_size
                / (1024 * 1024)
            )

            print(
                f"  OK  {item['file']:<32}"
                f"{size_mb:>8.2f} MB"
            )


    if missing_files:

        print(
            "\nERROR: Some generated files are missing."
        )

        for file_path in missing_files:
            print(f" - {file_path}")

        sys.exit(1)


    print(
        "\nAll required generated files exist."
    )


# ============================================================
# COPY CSV INTO POSTGRESQL
# ============================================================

def copy_csv_to_table(
    connection,
    table,
    columns,
    file_path,
):

    column_list = ", ".join(
        columns
    )


    copy_sql = f"""
        COPY {table}
        ({column_list})

        FROM STDIN

        WITH (
            FORMAT CSV,
            HEADER TRUE,
            NULL ''
        );
    """


    start_time = time.perf_counter()


    with connection.cursor() as cursor:

        with cursor.copy(
            copy_sql
        ) as copy:

            with open(
                file_path,
                mode="r",
                encoding="utf-8",
                newline="",
            ) as csv_file:

                while True:

                    chunk = csv_file.read(
                        1024 * 1024
                    )

                    if not chunk:
                        break

                    copy.write(
                        chunk
                    )


    elapsed = (
        time.perf_counter()
        - start_time
    )


    return elapsed


# ============================================================
# CLEAR CURRENT DATA
#
# Makes the loader safely rerunnable.
# ============================================================

def truncate_tables(
    connection
):

    print(
        "\nClearing existing analytics data..."
    )


    truncate_sql = """
        TRUNCATE TABLE

            analytics.fact_promotions,
            analytics.fact_targets_monthly,
            analytics.fact_inventory_daily,
            analytics.fact_sales_daily,

            analytics.dim_salesperson,
            analytics.dim_product,
            analytics.dim_store,
            analytics.dim_date

        RESTART IDENTITY
        CASCADE;
    """


    with connection.cursor() as cursor:

        cursor.execute(
            truncate_sql
        )


    print(
        "Existing data cleared."
    )


# ============================================================
# GET TABLE ROW COUNT
# ============================================================

def get_row_count(
    connection,
    table
):

    with connection.cursor() as cursor:

        cursor.execute(
            f"SELECT COUNT(*) FROM {table};"
        )

        result = cursor.fetchone()


    return result[0]


# ============================================================
# POST-LOAD VALIDATION
# ============================================================

def validate_loaded_data(
    connection
):

    print(
        "\n============================================"
    )

    print(
        "POST-LOAD VALIDATION"
    )

    print(
        "============================================"
    )


    results = {}


    for item in TABLES:

        table = item["table"]

        count = get_row_count(
            connection,
            table
        )

        results[table] = count

        print(
            f"{table:<42}"
            f"{count:>12,}"
        )


    # --------------------------------------------------------
    # Exact dimension checks
    # --------------------------------------------------------

    print(
        "\nChecking fixed table counts..."
    )


    all_fixed_counts_valid = True


    for table, expected in (
        EXPECTED_FIXED_COUNTS.items()
    ):

        actual = results[
            table
        ]


        if actual == expected:

            print(
                f"  PASS {table}: "
                f"{actual:,}"
            )

        else:

            print(
                f"  FAIL {table}: "
                f"expected {expected:,}, "
                f"found {actual:,}"
            )

            all_fixed_counts_valid = False


    # --------------------------------------------------------
    # Sales / inventory relationship
    # --------------------------------------------------------

    sales_count = results[
        "analytics.fact_sales_daily"
    ]

    inventory_count = results[
        "analytics.fact_inventory_daily"
    ]


    print(
        "\nChecking sales / inventory consistency..."
    )


    if (
        sales_count
        == inventory_count
        == 449_979
    ):

        print(
            "  PASS Sales and inventory both "
            "contain 449,979 rows."
        )

    else:

        print(
            "  WARNING Expected generated count "
            "was 449,979."
        )

        print(
            f"          Sales:     {sales_count:,}"
        )

        print(
            f"          Inventory: {inventory_count:,}"
        )


    # --------------------------------------------------------
    # Date coverage
    # --------------------------------------------------------

    with connection.cursor() as cursor:

        cursor.execute(
            """
            SELECT
                MIN(date_id),
                MAX(date_id),
                COUNT(DISTINCT date_id)
            FROM analytics.fact_sales_daily;
            """
        )

        (
            min_date,
            max_date,
            distinct_dates,
        ) = cursor.fetchone()


    print(
        "\nDate coverage:"
    )

    print(
        f"  First date:     {min_date}"
    )

    print(
        f"  Last date:      {max_date}"
    )

    print(
        f"  Distinct dates: {distinct_dates:,}"
    )


    return (
        all_fixed_counts_valid
        and sales_count > 0
        and inventory_count > 0
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print(
        "\n============================================"
    )

    print(
        "AI BUSINESS INTELLIGENCE ANALYST"
    )

    print(
        "POSTGRESQL DATA LOADER"
    )

    print(
        "============================================"
    )


    print(
        f"\nProject root:\n{ROOT}"
    )

    print(
        f"\nGenerated data directory:\n{DATA_DIR}"
    )


    # --------------------------------------------------------
    # Step 1: Files
    # --------------------------------------------------------

    validate_files()


    # --------------------------------------------------------
    # Step 2: Database connection
    # --------------------------------------------------------

    print(
        "\nConnecting to PostgreSQL..."
    )


    try:

        with psycopg.connect(
            **DB_CONFIG
        ) as connection:


            print(
                "Database connection successful."
            )


            with connection.cursor() as cursor:

                cursor.execute(
                    """
                    SELECT
                        current_database(),
                        current_user;
                    """
                )

                (
                    current_database,
                    current_user,
                ) = cursor.fetchone()


            print(
                f"Database: {current_database}"
            )

            print(
                f"User:     {current_user}"
            )


            # ------------------------------------------------
            # Step 3: Clear existing records
            # ------------------------------------------------

            truncate_tables(
                connection
            )


            # ------------------------------------------------
            # Step 4: Load tables
            # ------------------------------------------------

            print(
                "\nLoading generated data..."
            )


            for index, item in enumerate(
                TABLES,
                start=1,
            ):

                table = item[
                    "table"
                ]

                file_path = (
                    DATA_DIR
                    / item["file"]
                )


                print(
                    f"\n[{index}/{len(TABLES)}] "
                    f"Loading {table}..."
                )


                elapsed = copy_csv_to_table(
                    connection=connection,
                    table=table,
                    columns=item["columns"],
                    file_path=file_path,
                )


                count = get_row_count(
                    connection,
                    table,
                )


                print(
                    f"    Loaded {count:,} rows "
                    f"in {elapsed:.2f} seconds."
                )


            # ------------------------------------------------
            # Step 5: Validation
            # ------------------------------------------------

            validation_passed = (
                validate_loaded_data(
                    connection
                )
            )


            # ------------------------------------------------
            # Connection context commits here if no exception
            # occurred.
            # ------------------------------------------------


            print(
                "\n============================================"
            )

            if validation_passed:

                print(
                    "DATA LOAD COMPLETED SUCCESSFULLY"
                )

            else:

                print(
                    "DATA LOAD COMPLETED WITH WARNINGS"
                )

            print(
                "============================================"
            )


    except Exception as error:

        print(
            "\n============================================"
        )

        print(
            "DATA LOAD FAILED"
        )

        print(
            "============================================"
        )

        print(
            f"\nError type: "
            f"{type(error).__name__}"
        )

        print(
            f"\nError:\n{error}"
        )

        raise


if __name__ == "__main__":

    main()