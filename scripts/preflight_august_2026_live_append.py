from __future__ import annotations

import json
import sys

from pathlib import Path
from typing import Any

import pandas as pd

from sqlalchemy import text


# ============================================================
# PROJECT ROOT
# ============================================================

PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[1]
)


if str(PROJECT_ROOT) not in sys.path:

    sys.path.insert(
        0,
        str(
            PROJECT_ROOT
        ),
    )


# ============================================================
# APPLICATION IMPORTS
# ============================================================

from backend.app.database import engine

from backend.app.ingestion.reader import (
    read_source_dataframe,
)


# ============================================================
# FILE LOCATIONS
# ============================================================

VALIDATION_DIR = (
    PROJECT_ROOT
    /
    "data"
    /
    "validation"
    /
    "august_2026"
)


GENERATED_CSV = (
    VALIDATION_DIR
    /
    "august_2026_sales_append.csv"
)


ROWS_ONLY_CSV = (
    VALIDATION_DIR
    /
    "august_2026_sales_append_rows_only.csv"
)


PREFLIGHT_MANIFEST = (
    VALIDATION_DIR
    /
    "august_2026_live_append_preflight.json"
)


# ============================================================
# EXPECTED SOURCE SCHEMA
# ============================================================

EXPECTED_HEADERS = [
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
]


# ============================================================
# NATURAL RECORD KEY
# ============================================================

NATURAL_KEY = [
    "date_id",
    "store_id",
    "product_id",
    "salesperson_id",
]


# ============================================================
# EXPECTED PERIOD
# ============================================================

EXPECTED_START = (
    "2026-08-01"
)

EXPECTED_END = (
    "2026-08-31"
)


EXPECTED_AUGUST_ROWS = (
    24_260
)


# ============================================================
# HELPERS
# ============================================================

def json_safe(
    value: Any,
) -> Any:

    if isinstance(
        value,
        pd.Timestamp,
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
        list,
    ):

        return [
            json_safe(
                item
            )

            for item
            in value
        ]

    return value


def normalize_header(
    value: Any,
) -> str:

    return (
        str(
            value
        )
        .strip()
        .casefold()
    )


def normalize_headers(
    headers: list[Any],
) -> list[str]:

    return [
        normalize_header(
            header
        )
        for header
        in headers
    ]


def headers_match(
    actual_headers: list[Any],
    expected_headers: list[Any],
) -> bool:

    return (
        normalize_headers(
            actual_headers
        )
        ==
        normalize_headers(
            expected_headers
        )
    )


def add_check(
    checks: list[dict],
    name: str,
    passed: bool,
    actual: Any = None,
    expected: Any = None,
    detail: str | None = None,
) -> None:

    checks.append(
        {
            "check":
                name,

            "status":
                (
                    "PASS"
                    if passed
                    else
                    "FAIL"
                ),

            "actual":
                json_safe(
                    actual
                ),

            "expected":
                json_safe(
                    expected
                ),

            "detail":
                detail,
        }
    )


# ============================================================
# GOOGLE SOURCE
# ============================================================

def get_active_google_sales_source() -> dict:

    query = text(
        """
        SELECT
            source_id,
            source_name,
            source_type,
            source_location,
            sheet_name,
            is_active,
            load_strategy,
            mapping_status,
            schema_fingerprint,
            last_successful_refresh,
            last_refresh_status

        FROM
            analytics.data_sources

        WHERE
            is_active =
                TRUE

            AND

            source_type =
                'google_sheets'

            AND

            LOWER(
                COALESCE(
                    sheet_name,
                    ''
                )
            )
            =
            'sales'

        ORDER BY
            source_id;
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

    if not rows:

        raise RuntimeError(
            (
                "No active Google Sheets Sales source "
                "was found in analytics.data_sources."
            )
        )

    if (
        len(
            rows
        )
        >
        1
    ):

        source_ids = [
            int(
                row[
                    "source_id"
                ]
            )
            for row
            in rows
        ]

        raise RuntimeError(
            (
                "More than one active Google Sheets "
                "Sales source exists. "
                f"Source IDs: {source_ids}."
            )
        )

    return dict(
        rows[
            0
        ]
    )


# ============================================================
# LAST SUCCESSFUL REFRESH
# ============================================================

def get_last_successful_refresh(
    source_id: int,
) -> dict | None:

    query = text(
        """
        SELECT
            refresh_id,
            source_id,
            status,
            rows_read,
            rows_inserted,
            rows_updated,
            rows_unchanged,
            rows_rejected,
            started_at,
            finished_at

        FROM
            analytics.data_refresh_runs

        WHERE
            source_id =
                :source_id

            AND

            status =
                'success'

        ORDER BY
            refresh_id DESC

        LIMIT 1;
        """
    )

    with engine.connect() as connection:

        row = (
            connection
            .execute(
                query,
                {
                    "source_id":
                        source_id,
                },
            )
            .mappings()
            .one_or_none()
        )

    if row is None:

        return None

    return dict(
        row
    )


# ============================================================
# WAREHOUSE STATE
# ============================================================

def get_warehouse_state() -> dict:

    query = text(
        """
        SELECT
            COUNT(*)
                AS total_rows,

            MIN(date_id)
                AS minimum_date,

            MAX(date_id)
                AS maximum_date,

            COUNT(*)
                FILTER
                (
                    WHERE
                        date_id
                        BETWEEN
                            DATE '2026-08-01'
                            AND
                            DATE '2026-08-31'
                )
                AS august_rows

        FROM
            analytics.fact_sales_daily;
        """
    )

    with engine.connect() as connection:

        row = (
            connection
            .execute(
                query
            )
            .mappings()
            .one()
        )

    return dict(
        row
    )


# ============================================================
# DIMENSION IDS
# ============================================================

def get_dimension_ids(
    table_name: str,
    id_column: str,
) -> set[int]:

    allowed = {
        (
            "dim_store",
            "store_id",
        ),
        (
            "dim_product",
            "product_id",
        ),
        (
            "dim_salesperson",
            "salesperson_id",
        ),
    }

    if (
        table_name,
        id_column,
    ) not in allowed:

        raise ValueError(
            "Unsupported dimension lookup."
        )

    query = text(
        f"""
        SELECT
            {id_column}

        FROM
            analytics.{table_name};
        """
    )

    with engine.connect() as connection:

        values = (
            connection
            .execute(
                query
            )
            .scalars()
            .all()
        )

    return {
        int(
            value
        )
        for value
        in values
    }


# ============================================================
# LOCAL AUGUST FILE
# ============================================================

def load_generated_august() -> pd.DataFrame:

    if not GENERATED_CSV.exists():

        raise FileNotFoundError(
            (
                "Generated August file does not exist: "
                f"{GENERATED_CSV}"
            )
        )

    return pd.read_csv(
        GENERATED_CSV
    )


# ============================================================
# LIVE GOOGLE SOURCE
# ============================================================

def load_live_google_source(
    source: dict,
) -> pd.DataFrame:

    print()
    print(
        "Reading current live Google Sheets source..."
    )

    print(
        (
            "This can take some time because the "
            "preflight intentionally reads the "
            "complete source."
        )
    )

    return (
        read_source_dataframe(
            source
        )
    )


# ============================================================
# NORMALIZE NATURAL KEY
# ============================================================

def normalize_key_frame(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:

    result = (
        dataframe[
            NATURAL_KEY
        ]
        .copy()
    )

    result[
        "date_id"
    ] = (
        pd.to_datetime(
            result[
                "date_id"
            ],
            errors="raise",
        )
        .dt.strftime(
            "%Y-%m-%d"
        )
    )

    for column in (
        "store_id",
        "product_id",
        "salesperson_id",
    ):

        result[
            column
        ] = (
            pd.to_numeric(
                result[
                    column
                ],
                errors="raise",
            )
            .astype(
                "int64"
            )
        )

    return result


# ============================================================
# MAIN PREFLIGHT
# ============================================================

def run_preflight() -> dict:

    checks: list[dict] = []

    print()
    print(
        "="
        *
        72
    )

    print(
        "AUGUST 2026 LIVE APPEND PREFLIGHT"
    )

    print(
        "="
        *
        72
    )

    # --------------------------------------------------------
    # GENERATED FILE
    # --------------------------------------------------------

    local = (
        load_generated_august()
    )

    local_headers = list(
        local.columns
    )

    add_check(
        checks,
        "generated_headers",
        headers_match(
            local_headers,
            EXPECTED_HEADERS,
        ),
        actual=
            local_headers,
        expected=
            EXPECTED_HEADERS,
        detail=
            (
                "Header comparison is case-insensitive "
                "but column order must match."
            ),
    )

    add_check(
        checks,
        "generated_row_count",
        len(
            local
        )
        ==
        EXPECTED_AUGUST_ROWS,
        actual=
            len(
                local
            ),
        expected=
            EXPECTED_AUGUST_ROWS,
    )

    # --------------------------------------------------------
    # DATE RANGE
    # --------------------------------------------------------

    local_dates = (
        pd.to_datetime(
            local[
                "date_id"
            ],
            errors="raise",
        )
    )

    local_min_date = (
        local_dates
        .min()
        .strftime(
            "%Y-%m-%d"
        )
    )

    local_max_date = (
        local_dates
        .max()
        .strftime(
            "%Y-%m-%d"
        )
    )

    add_check(
        checks,
        "generated_min_date",
        local_min_date
        ==
        EXPECTED_START,
        actual=
            local_min_date,
        expected=
            EXPECTED_START,
    )

    add_check(
        checks,
        "generated_max_date",
        local_max_date
        ==
        EXPECTED_END,
        actual=
            local_max_date,
        expected=
            EXPECTED_END,
    )

    # --------------------------------------------------------
    # GENERATED KEY DUPLICATES
    # --------------------------------------------------------

    local_keys = (
        normalize_key_frame(
            local
        )
    )

    local_duplicate_count = int(
        local_keys
        .duplicated(
            subset=
                NATURAL_KEY,
            keep=False,
        )
        .sum()
    )

    add_check(
        checks,
        "generated_natural_key_duplicates",
        local_duplicate_count
        ==
        0,
        actual=
            local_duplicate_count,
        expected=
            0,
    )

    # --------------------------------------------------------
    # FINANCIAL IDENTITY
    # --------------------------------------------------------

    gross = pd.to_numeric(
        local[
            "gross_sales"
        ],
        errors="raise",
    )

    discount = pd.to_numeric(
        local[
            "discount_amount"
        ],
        errors="raise",
    )

    net = pd.to_numeric(
        local[
            "net_sales"
        ],
        errors="raise",
    )

    maximum_identity_difference = float(
        (
            (
                gross
                -
                discount
            )
            -
            net
        )
        .abs()
        .max()
    )

    add_check(
        checks,
        "financial_identity",
        maximum_identity_difference
        <=
        0.02,
        actual=
            round(
                maximum_identity_difference,
                6,
            ),
        expected=
            "<= 0.02",
    )

    # --------------------------------------------------------
    # DIMENSION INTEGRITY
    # --------------------------------------------------------

    valid_store_ids = (
        get_dimension_ids(
            "dim_store",
            "store_id",
        )
    )

    valid_product_ids = (
        get_dimension_ids(
            "dim_product",
            "product_id",
        )
    )

    valid_salesperson_ids = (
        get_dimension_ids(
            "dim_salesperson",
            "salesperson_id",
        )
    )

    generated_store_ids = {
        int(
            value
        )
        for value
        in pd.to_numeric(
            local[
                "store_id"
            ],
            errors="raise",
        )
        .unique()
    }

    generated_product_ids = {
        int(
            value
        )
        for value
        in pd.to_numeric(
            local[
                "product_id"
            ],
            errors="raise",
        )
        .unique()
    }

    generated_salesperson_ids = {
        int(
            value
        )
        for value
        in pd.to_numeric(
            local[
                "salesperson_id"
            ],
            errors="raise",
        )
        .unique()
    }

    missing_store_ids = sorted(
        generated_store_ids
        -
        valid_store_ids
    )

    missing_product_ids = sorted(
        generated_product_ids
        -
        valid_product_ids
    )

    missing_salesperson_ids = sorted(
        generated_salesperson_ids
        -
        valid_salesperson_ids
    )

    add_check(
        checks,
        "store_dimension_integrity",
        not missing_store_ids,
        actual=
            missing_store_ids,
        expected=
            [],
    )

    add_check(
        checks,
        "product_dimension_integrity",
        not missing_product_ids,
        actual=
            missing_product_ids,
        expected=
            [],
    )

    add_check(
        checks,
        "salesperson_dimension_integrity",
        not missing_salesperson_ids,
        actual=
            missing_salesperson_ids,
        expected=
            [],
    )

    # --------------------------------------------------------
    # SOURCE CONFIGURATION
    # --------------------------------------------------------

    source = (
        get_active_google_sales_source()
    )

    source_id = int(
        source[
            "source_id"
        ]
    )

    add_check(
        checks,
        "google_source_load_strategy",
        str(
            source.get(
                "load_strategy"
            )
        )
        .casefold()
        ==
        "upsert",
        actual=
            source.get(
                "load_strategy"
            ),
        expected=
            "upsert",
    )

    # --------------------------------------------------------
    # LIVE GOOGLE SHEET
    # --------------------------------------------------------

    live = (
        load_live_google_source(
            source
        )
    )

    live_headers = list(
        live.columns
    )

    add_check(
        checks,
        "live_google_headers",
        headers_match(
            live_headers,
            EXPECTED_HEADERS,
        ),
        actual=
            live_headers,
        expected=
            EXPECTED_HEADERS,
        detail=
            (
                "Header comparison is case-insensitive. "
                "For example Net_sales and net_sales "
                "are treated as the same semantic field."
            ),
    )

    live_dates = (
        pd.to_datetime(
            live[
                "date_id"
            ],
            errors="raise",
        )
    )

    live_row_count = int(
        len(
            live
        )
    )

    live_max_date = (
        live_dates
        .max()
        .strftime(
            "%Y-%m-%d"
        )
    )

    live_august_rows = int(
        (
            (
                live_dates
                >=
                pd.Timestamp(
                    EXPECTED_START
                )
            )
            &
            (
                live_dates
                <=
                pd.Timestamp(
                    EXPECTED_END
                )
            )
        )
        .sum()
    )

    add_check(
        checks,
        "live_source_has_no_august_rows",
        live_august_rows
        ==
        0,
        actual=
            live_august_rows,
        expected=
            0,
    )

    add_check(
        checks,
        "live_source_max_date_before_append",
        live_max_date
        ==
        "2026-07-31",
        actual=
            live_max_date,
        expected=
            "2026-07-31",
    )

    # --------------------------------------------------------
    # KEY OVERLAP
    # --------------------------------------------------------

    live_keys = (
        normalize_key_frame(
            live
        )
    )

    local_index = (
        pd.MultiIndex.from_frame(
            local_keys[
                NATURAL_KEY
            ]
        )
    )

    live_index = (
        pd.MultiIndex.from_frame(
            live_keys[
                NATURAL_KEY
            ]
        )
    )

    overlap_count = int(
        local_index
        .isin(
            live_index
        )
        .sum()
    )

    add_check(
        checks,
        "generated_keys_not_already_in_live_source",
        overlap_count
        ==
        0,
        actual=
            overlap_count,
        expected=
            0,
    )

    # --------------------------------------------------------
    # WAREHOUSE
    # --------------------------------------------------------

    warehouse = (
        get_warehouse_state()
    )

    warehouse_total = int(
        warehouse[
            "total_rows"
        ]
    )

    warehouse_august_rows = int(
        warehouse[
            "august_rows"
        ]
    )

    warehouse_max_date = (
        warehouse[
            "maximum_date"
        ]
        .isoformat()
        if warehouse[
            "maximum_date"
        ]
        else None
    )

    add_check(
        checks,
        "warehouse_has_no_august_rows",
        warehouse_august_rows
        ==
        0,
        actual=
            warehouse_august_rows,
        expected=
            0,
    )

    add_check(
        checks,
        "warehouse_max_date_before_append",
        warehouse_max_date
        ==
        "2026-07-31",
        actual=
            warehouse_max_date,
        expected=
            "2026-07-31",
    )

    add_check(
        checks,
        "live_source_matches_warehouse_row_count",
        live_row_count
        ==
        warehouse_total,
        actual={
            "live_source_rows":
                live_row_count,

            "warehouse_rows":
                warehouse_total,
        },
        expected=
            "equal",
    )

    # --------------------------------------------------------
    # LAST SUCCESSFUL REFRESH
    # --------------------------------------------------------

    last_refresh = (
        get_last_successful_refresh(
            source_id
        )
    )

    if last_refresh:

        add_check(
            checks,
            "last_refresh_matches_live_source",
            int(
                last_refresh.get(
                    "rows_read"
                )
                or
                0
            )
            ==
            live_row_count,
            actual=
                int(
                    last_refresh.get(
                        "rows_read"
                    )
                    or
                    0
                ),
            expected=
                live_row_count,
        )

    else:

        add_check(
            checks,
            "last_refresh_available",
            False,
            actual=
                None,
            expected=
                "successful refresh record",
        )

    # --------------------------------------------------------
    # EXPECTED POST-APPEND STATE
    # --------------------------------------------------------

    expected_post_append = {
        "source_id":
            source_id,

        "source_name":
            source[
                "source_name"
            ],

        "current_source_rows":
            live_row_count,

        "generated_august_rows":
            len(
                local
            ),

        "expected_rows_read_after_append":
            (
                live_row_count
                +
                len(
                    local
                )
            ),

        "expected_rows_inserted":
            len(
                local
            ),

        "expected_rows_updated":
            0,

        "expected_rows_unchanged":
            live_row_count,

        "expected_rows_rejected":
            0,

        "expected_warehouse_total":
            (
                warehouse_total
                +
                len(
                    local
                )
            ),

        "expected_warehouse_august_rows":
            len(
                local
            ),

        "expected_data_through":
            EXPECTED_END,
    }

    # --------------------------------------------------------
    # FINAL STATUS
    # --------------------------------------------------------

    failed_checks = [
        check
        for check
        in checks
        if (
            check[
                "status"
            ]
            ==
            "FAIL"
        )
    ]

    overall_status = (
        "PASS"
        if not failed_checks
        else
        "FAIL"
    )

    result = {
        "status":
            overall_status,

        "generated_file":
            str(
                GENERATED_CSV
            ),

        "google_source": {
            "source_id":
                source_id,

            "source_name":
                source[
                    "source_name"
                ],

            "sheet_name":
                source[
                    "sheet_name"
                ],

            "load_strategy":
                source[
                    "load_strategy"
                ],
        },

        "checks":
            checks,

        "expected_post_append":
            expected_post_append,
    }

    # --------------------------------------------------------
    # PRODUCE HEADERLESS APPEND FILE ONLY IF SAFE
    # --------------------------------------------------------

    if (
        overall_status
        ==
        "PASS"
    ):

        local.to_csv(
            ROWS_ONLY_CSV,
            index=False,
            header=False,
            encoding="utf-8",
        )

        result[
            "rows_only_append_file"
        ] = str(
            ROWS_ONLY_CSV
        )

    PREFLIGHT_MANIFEST.write_text(
        json.dumps(
            json_safe(
                result
            ),
            indent=2,
            default=str,
        ),
        encoding="utf-8",
    )

    print()
    print(
        json.dumps(
            json_safe(
                result
            ),
            indent=2,
            default=str,
        )
    )

    print()
    print(
        "="
        *
        72
    )

    if (
        overall_status
        ==
        "PASS"
    ):

        print(
            "PREFLIGHT PASSED"
        )

        print()
        print(
            (
                "The August file is safe to append "
                "to the current Google Sheets Sales tab."
            )
        )

        print()
        print(
            "Use this HEADERLESS append file:"
        )

        print(
            f"  {ROWS_ONLY_CSV}"
        )

    else:

        print(
            "PREFLIGHT FAILED"
        )

        print()
        print(
            (
                "Do NOT append August to Google Sheets "
                "until the failed checks are resolved."
            )
        )

    print(
        "="
        *
        72
    )

    return result


# ============================================================
# MAIN
# ============================================================

def main() -> int:

    result = (
        run_preflight()
    )

    return (
        0
        if (
            result[
                "status"
            ]
            ==
            "PASS"
        )
        else
        1
    )


if __name__ == "__main__":

    raise SystemExit(
        main()
    )