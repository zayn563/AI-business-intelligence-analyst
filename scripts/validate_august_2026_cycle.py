from __future__ import annotations

import argparse
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
# APPLICATION
# ============================================================

from backend.app.database import engine

from backend.app.decision.action_effectiveness import (
    evaluate_action,
    json_safe,
)


# ============================================================
# FILES
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


GENERATED_AUGUST_CSV = (
    VALIDATION_DIR
    /
    "august_2026_sales_append.csv"
)


EXPECTED_REGIONAL_CSV = (
    VALIDATION_DIR
    /
    "august_2026_regional_expected.csv"
)


PREFLIGHT_MANIFEST = (
    VALIDATION_DIR
    /
    "august_2026_live_append_preflight.json"
)


# ============================================================
# PERIOD
# ============================================================

AUGUST_START = (
    "2026-08-01"
)

AUGUST_END = (
    "2026-08-31"
)


# ============================================================
# NATURAL KEY
# ============================================================

NATURAL_KEY = [
    "date_id",
    "store_id",
    "product_id",
    "salesperson_id",
]


# ============================================================
# TOLERANCES
# ============================================================

MONEY_TOLERANCE = (
    0.10
)

PERCENT_TOLERANCE = (
    0.01
)


# ============================================================
# HELPERS
# ============================================================

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


def load_json(
    path: Path,
) -> dict:

    if not path.exists():

        raise FileNotFoundError(
            f"Required file missing: {path}"
        )

    return json.loads(
        path.read_text(
            encoding="utf-8"
        )
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
            load_strategy

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

    if (
        len(rows)
        !=
        1
    ):

        raise RuntimeError(
            (
                "Expected exactly one active "
                "Google Sheets Sales source; "
                f"found {len(rows)}."
            )
        )

    return dict(
        rows[
            0
        ]
    )


# ============================================================
# LAST REFRESH RUN
# ============================================================

def get_last_refresh(
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

    return (
        dict(row)
        if row
        else None
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

        return dict(
            connection
            .execute(
                query
            )
            .mappings()
            .one()
        )


# ============================================================
# AUGUST DUPLICATE KEY COUNT
# ============================================================

def get_august_duplicate_key_count() -> int:

    query = text(
        """
        SELECT
            COALESCE(
                SUM(
                    duplicate_count
                    -
                    1
                ),
                0
            )

        FROM
        (
            SELECT
                date_id,
                store_id,
                product_id,
                salesperson_id,
                COUNT(*)
                    AS duplicate_count

            FROM
                analytics.fact_sales_daily

            WHERE
                date_id
                BETWEEN
                    DATE '2026-08-01'
                    AND
                    DATE '2026-08-31'

            GROUP BY
                date_id,
                store_id,
                product_id,
                salesperson_id

            HAVING
                COUNT(*)
                >
                1
        )
            duplicates;
        """
    )

    with engine.connect() as connection:

        return int(
            connection
            .execute(
                query
            )
            .scalar_one()
            or
            0
        )


# ============================================================
# ACTUAL REGIONAL AUGUST METRICS
# ============================================================

def get_actual_regional_metrics() -> pd.DataFrame:

    query = text(
        """
        SELECT
            s.region,

            SUM(
                f.gross_sales
            )
                AS gross_sales,

            SUM(
                f.discount_amount
            )
                AS discount_amount,

            SUM(
                f.net_sales
            )
                AS net_sales,

            SUM(
                f.cogs
            )
                AS cogs,

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
                AS margin_pct

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
                DATE '2026-08-01'
                AND
                DATE '2026-08-31'

        GROUP BY
            s.region

        ORDER BY
            s.region;
        """
    )

    return pd.read_sql_query(
        query,
        engine,
    )


# ============================================================
# PRODUCT 10 WAREHOUSE TOTALS
# ============================================================

def get_product_10_actual() -> dict:

    query = text(
        """
        SELECT
            SUM(net_sales)
                AS net_sales,

            SUM(
                net_sales
                -
                cogs
            )
                AS gross_profit,

            SUM(units_sold)
                AS units_sold

        FROM
            analytics.fact_sales_daily

        WHERE
            date_id
            BETWEEN
                DATE '2026-08-01'
                AND
                DATE '2026-08-31'

            AND

            product_id =
                10;
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

    return {
        "net_sales":
            float(
                row[
                    "net_sales"
                ]
                or
                0
            ),

        "gross_profit":
            float(
                row[
                    "gross_profit"
                ]
                or
                0
            ),

        "units_sold":
            float(
                row[
                    "units_sold"
                ]
                or
                0
            ),
    }


# ============================================================
# PRODUCT 10 LOCAL EXPECTED TOTALS
# ============================================================

def get_product_10_expected() -> dict:

    dataframe = pd.read_csv(
        GENERATED_AUGUST_CSV
    )

    product_id = pd.to_numeric(
        dataframe[
            "product_id"
        ],
        errors="raise",
    )

    subset = dataframe[
        product_id
        ==
        10
    ].copy()

    net_sales = pd.to_numeric(
        subset[
            "net_sales"
        ],
        errors="raise",
    )

    cogs = pd.to_numeric(
        subset[
            "cogs"
        ],
        errors="raise",
    )

    units = pd.to_numeric(
        subset[
            "units_sold"
        ],
        errors="raise",
    )

    return {
        "net_sales":
            float(
                net_sales.sum()
            ),

        "gross_profit":
            float(
                (
                    net_sales
                    -
                    cogs
                )
                .sum()
            ),

        "units_sold":
            float(
                units.sum()
            ),
    }


# ============================================================
# REGIONAL COMPARISON
# ============================================================

def compare_regional_metrics() -> tuple[
    bool,
    list[dict],
]:

    expected = pd.read_csv(
        EXPECTED_REGIONAL_CSV
    )

    actual = (
        get_actual_regional_metrics()
    )

    expected[
        "region"
    ] = (
        expected[
            "region"
        ]
        .astype(str)
        .str.strip()
    )

    actual[
        "region"
    ] = (
        actual[
            "region"
        ]
        .astype(str)
        .str.strip()
    )

    merged = (
        expected.merge(
            actual,
            on="region",
            how="outer",
            suffixes=(
                "_expected",
                "_actual",
            ),
        )
    )

    details: list[dict] = []

    all_passed = True

    for (
        _,
        row,
    ) in merged.iterrows():

        region = str(
            row[
                "region"
            ]
        )

        region_checks: list[dict] = []

        for metric in (
            "net_sales",
            "gross_profit",
            "gross_sales",
            "cogs",
        ):

            expected_value = float(
                row[
                    f"{metric}_expected"
                ]
            )

            actual_value = float(
                row[
                    f"{metric}_actual"
                ]
            )

            difference = abs(
                expected_value
                -
                actual_value
            )

            passed = (
                difference
                <=
                MONEY_TOLERANCE
            )

            region_checks.append(
                {
                    "metric":
                        metric,

                    "expected":
                        round(
                            expected_value,
                            4,
                        ),

                    "actual":
                        round(
                            actual_value,
                            4,
                        ),

                    "difference":
                        round(
                            difference,
                            6,
                        ),

                    "status":
                        (
                            "PASS"
                            if passed
                            else
                            "FAIL"
                        ),
                }
            )

            if not passed:

                all_passed = False

        for metric in (
            "units_sold",
            "transactions",
        ):

            expected_value = int(
                round(
                    float(
                        row[
                            f"{metric}_expected"
                        ]
                    )
                )
            )

            actual_value = int(
                round(
                    float(
                        row[
                            f"{metric}_actual"
                        ]
                    )
                )
            )

            passed = (
                expected_value
                ==
                actual_value
            )

            region_checks.append(
                {
                    "metric":
                        metric,

                    "expected":
                        expected_value,

                    "actual":
                        actual_value,

                    "status":
                        (
                            "PASS"
                            if passed
                            else
                            "FAIL"
                        ),
                }
            )

            if not passed:

                all_passed = False

        expected_margin = float(
            row[
                "margin_pct_expected"
            ]
        )

        actual_margin = float(
            row[
                "margin_pct_actual"
            ]
        )

        margin_difference = abs(
            expected_margin
            -
            actual_margin
        )

        margin_passed = (
            margin_difference
            <=
            PERCENT_TOLERANCE
        )

        region_checks.append(
            {
                "metric":
                    "margin_pct",

                "expected":
                    round(
                        expected_margin,
                        6,
                    ),

                "actual":
                    round(
                        actual_margin,
                        6,
                    ),

                "difference":
                    round(
                        margin_difference,
                        6,
                    ),

                "status":
                    (
                        "PASS"
                        if margin_passed
                        else
                        "FAIL"
                    ),
            }
        )

        if not margin_passed:

            all_passed = False

        details.append(
            {
                "region":
                    region,

                "checks":
                    region_checks,
            }
        )

    return (
        all_passed,
        details,
    )


# ============================================================
# MAIN VALIDATOR
# ============================================================

def validate(
    action_id: int | None,
    persist_action_outcome: bool,
) -> dict:

    checks: list[dict] = []

    print()
    print(
        "="
        *
        72
    )

    print(
        "AUGUST 2026 LIVE INGESTION VALIDATION"
    )

    print(
        "="
        *
        72
    )

    preflight = (
        load_json(
            PREFLIGHT_MANIFEST
        )
    )

    expected = (
        preflight[
            "expected_post_append"
        ]
    )

    source = (
        get_active_google_sales_source()
    )

    source_id = int(
        source[
            "source_id"
        ]
    )

    # --------------------------------------------------------
    # LAST REFRESH
    # --------------------------------------------------------

    refresh = (
        get_last_refresh(
            source_id
        )
    )

    if refresh is None:

        add_check(
            checks,
            "post_append_refresh_exists",
            False,
            actual=
                None,
            expected=
                "refresh record",
        )

    else:

        add_check(
            checks,
            "refresh_status",
            refresh[
                "status"
            ]
            ==
            "success",
            actual=
                refresh[
                    "status"
                ],
            expected=
                "success",
        )

        for field in (
            "rows_read",
            "rows_inserted",
            "rows_updated",
            "rows_unchanged",
            "rows_rejected",
        ):

            expected_field = (
                {
                    "rows_read":
                        "expected_rows_read_after_append",

                    "rows_inserted":
                        "expected_rows_inserted",

                    "rows_updated":
                        "expected_rows_updated",

                    "rows_unchanged":
                        "expected_rows_unchanged",

                    "rows_rejected":
                        "expected_rows_rejected",
                }[
                    field
                ]
            )

            actual_value = int(
                refresh.get(
                    field
                )
                or
                0
            )

            expected_value = int(
                expected[
                    expected_field
                ]
            )

            add_check(
                checks,
                f"refresh_{field}",
                actual_value
                ==
                expected_value,
                actual=
                    actual_value,
                expected=
                    expected_value,
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
        "warehouse_total_rows",
        warehouse_total
        ==
        int(
            expected[
                "expected_warehouse_total"
            ]
        ),
        actual=
            warehouse_total,
        expected=
            expected[
                "expected_warehouse_total"
            ],
    )

    add_check(
        checks,
        "warehouse_august_rows",
        warehouse_august_rows
        ==
        int(
            expected[
                "expected_warehouse_august_rows"
            ]
        ),
        actual=
            warehouse_august_rows,
        expected=
            expected[
                "expected_warehouse_august_rows"
            ],
    )

    add_check(
        checks,
        "warehouse_data_through",
        warehouse_max_date
        ==
        AUGUST_END,
        actual=
            warehouse_max_date,
        expected=
            AUGUST_END,
    )

    # --------------------------------------------------------
    # DUPLICATES
    # --------------------------------------------------------

    duplicate_count = (
        get_august_duplicate_key_count()
    )

    add_check(
        checks,
        "warehouse_august_natural_key_duplicates",
        duplicate_count
        ==
        0,
        actual=
            duplicate_count,
        expected=
            0,
    )

    # --------------------------------------------------------
    # EXACT REGIONAL AGGREGATES
    # --------------------------------------------------------

    (
        regional_passed,
        regional_details,
    ) = (
        compare_regional_metrics()
    )

    add_check(
        checks,
        "regional_aggregate_reconciliation",
        regional_passed,
        actual=
            regional_details,
        expected=
            "warehouse equals generated August file",
    )

    # --------------------------------------------------------
    # PRODUCT 10
    # --------------------------------------------------------

    expected_product_10 = (
        get_product_10_expected()
    )

    actual_product_10 = (
        get_product_10_actual()
    )

    product_checks: list[dict] = []

    product_passed = True

    for metric in (
        "net_sales",
        "gross_profit",
    ):

        difference = abs(
            actual_product_10[
                metric
            ]
            -
            expected_product_10[
                metric
            ]
        )

        passed = (
            difference
            <=
            MONEY_TOLERANCE
        )

        product_checks.append(
            {
                "metric":
                    metric,

                "expected":
                    round(
                        expected_product_10[
                            metric
                        ],
                        4,
                    ),

                "actual":
                    round(
                        actual_product_10[
                            metric
                        ],
                        4,
                    ),

                "difference":
                    round(
                        difference,
                        6,
                    ),

                "status":
                    (
                        "PASS"
                        if passed
                        else
                        "FAIL"
                    ),
            }
        )

        if not passed:

            product_passed = False

    expected_units = int(
        round(
            expected_product_10[
                "units_sold"
            ]
        )
    )

    actual_units = int(
        round(
            actual_product_10[
                "units_sold"
            ]
        )
    )

    units_passed = (
        expected_units
        ==
        actual_units
    )

    product_checks.append(
        {
            "metric":
                "units_sold",

            "expected":
                expected_units,

            "actual":
                actual_units,

            "status":
                (
                    "PASS"
                    if units_passed
                    else
                    "FAIL"
                ),
        }
    )

    if not units_passed:

        product_passed = False

    add_check(
        checks,
        "product_10_reconciliation",
        product_passed,
        actual=
            product_checks,
        expected=
            "warehouse equals generated August file",
    )

    # --------------------------------------------------------
    # ACTION EFFECTIVENESS
    # --------------------------------------------------------

    action_result = None

    if (
        action_id
        is not None
    ):

        # Persist only if ingestion checks are already clean.

        failures_before_action = [
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

        should_persist = (
            persist_action_outcome

            and

            not failures_before_action
        )

        action_result = (
            evaluate_action(
                action_id=
                    action_id,

                persist=
                    should_persist,
            )
        )

        action_status = (
            action_result.get(
                "status"
            )
        )

        action_passed = (
            action_status
            ==
            "IMPROVED"
        )

        add_check(
            checks,
            "controlled_south_action_effectiveness",
            action_passed,
            actual=
                action_result,
            expected=
                (
                    "IMPROVED for controlled "
                    "South recovery"
                ),
            detail=
                (
                    "No causal attribution is claimed. "
                    "The test only checks whether the "
                    "linked KPI improved after the "
                    "baseline period."
                ),
        )

    # --------------------------------------------------------
    # OVERALL
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

    status = (
        "PASS"
        if not failed_checks
        else
        "FAIL"
    )

    result = {
        "status":
            status,

        "source_id":
            source_id,

        "checks":
            checks,

        "action_result":
            action_result,

        "summary": {
            "checks":
                len(
                    checks
                ),

            "failures":
                len(
                    failed_checks
                ),
        },
    }

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
        status
        ==
        "PASS"
    ):

        print(
            "AUGUST INGESTION VALIDATION PASSED"
        )

    else:

        print(
            "AUGUST INGESTION VALIDATION FAILED"
        )

    print(
        "="
        *
        72
    )

    return result


# ============================================================
# CLI
# ============================================================

def build_parser() -> argparse.ArgumentParser:

    parser = argparse.ArgumentParser(
        description=(
            "Validate August 2026 live-source "
            "ingestion and optional Action "
            "Effectiveness outcome."
        )
    )

    parser.add_argument(
        "--action-id",
        type=int,
        default=None,
        help=(
            "Tracked management action to evaluate."
        ),
    )

    parser.add_argument(
        "--persist-action-outcome",
        action="store_true",
        help=(
            "Persist the Action Effectiveness result "
            "only if all prior ingestion checks pass."
        ),
    )

    return parser


# ============================================================
# MAIN
# ============================================================

def main() -> int:

    parser = (
        build_parser()
    )

    args = (
        parser.parse_args()
    )

    result = (
        validate(
            action_id=
                args.action_id,

            persist_action_outcome=
                args.persist_action_outcome,
        )
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