from __future__ import annotations

import argparse
import json
import sys

from datetime import date

from pathlib import Path

from typing import Any

import pandas as pd

from sqlalchemy import (
    inspect,
    text,
)


# ============================================================
# PROJECT ROOT
# ============================================================

PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[1]
)


if (
    str(PROJECT_ROOT)
    not in
    sys.path
):

    sys.path.insert(
        0,
        str(PROJECT_ROOT),
    )


# ============================================================
# APPLICATION DATABASE
# ============================================================

from backend.app.database import engine


# ============================================================
# PERIODS
# ============================================================

SOURCE_START = date(
    2026,
    7,
    1,
)

SOURCE_END = date(
    2026,
    7,
    31,
)


TARGET_START = date(
    2026,
    8,
    1,
)

TARGET_END = date(
    2026,
    8,
    31,
)


# ============================================================
# OUTPUT DIRECTORY
# ============================================================

DEFAULT_OUTPUT_DIR = (
    PROJECT_ROOT
    /
    "data"
    /
    "validation"
    /
    "august_2026"
)


# ============================================================
# CORE COLUMN NAMES
# ============================================================

DATE_COLUMN = (
    "date_id"
)

STORE_COLUMN = (
    "store_id"
)

PRODUCT_COLUMN = (
    "product_id"
)

SALESPERSON_COLUMN = (
    "salesperson_id"
)


# ============================================================
# METRIC COLUMN NAMES
# ============================================================

GROSS_SALES_COLUMN = (
    "gross_sales"
)

DISCOUNT_COLUMN = (
    "discount_amount"
)

NET_SALES_COLUMN = (
    "net_sales"
)

UNITS_COLUMN = (
    "units_sold"
)

TRANSACTIONS_COLUMN = (
    "transactions"
)

COGS_COLUMN = (
    "cogs"
)


# ============================================================
# SCALABLE NUMERIC COLUMNS
#
# IMPORTANT:
#
# Warehouse source columns may be integer typed.
#
# Scenario factors such as 1.08 or 0.93 create decimal values.
# Pandas 2.x correctly rejects assigning those decimal values
# into int64 columns.
#
# We therefore convert all scenario-scaled measures to float64
# BEFORE applying any scenario transformation.
#
# Integer business measures are converted back to integers
# after all transformations are complete.
# ============================================================

SCALABLE_NUMERIC_COLUMNS = (
    GROSS_SALES_COLUMN,
    DISCOUNT_COLUMN,
    NET_SALES_COLUMN,
    UNITS_COLUMN,
    TRANSACTIONS_COLUMN,
    COGS_COLUMN,
)


# ============================================================
# REGIONAL SCENARIOS
# ============================================================

REGIONAL_SCENARIOS = {
    "South": {
        "gross_sales_factor":
            1.12,

        "units_factor":
            1.08,

        "transactions_factor":
            1.06,

        "discount_factor":
            0.75,

        "cogs_factor":
            0.99,

        "description":
            (
                "Controlled profitability recovery: "
                "sales and volume improve while "
                "discount pressure is reduced."
            ),
    },

    "East": {
        "gross_sales_factor":
            0.92,

        "units_factor":
            0.93,

        "transactions_factor":
            0.94,

        "discount_factor":
            1.03,

        "cogs_factor":
            0.95,

        "description":
            (
                "Controlled deterioration: sales "
                "and volume weaken further."
            ),
    },

    "North": {
        "gross_sales_factor":
            1.04,

        "units_factor":
            1.03,

        "transactions_factor":
            1.02,

        "discount_factor":
            1.00,

        "cogs_factor":
            1.03,

        "description":
            (
                "Positive growth continues but "
                "at a more moderate pace."
            ),
    },

    "West": {
        "gross_sales_factor":
            0.80,

        "units_factor":
            0.83,

        "transactions_factor":
            0.86,

        "discount_factor":
            1.06,

        "cogs_factor":
            0.86,

        "description":
            (
                "New material deterioration designed "
                "to create a new August risk."
            ),
    },

    "Central": {
        "gross_sales_factor":
            1.01,

        "units_factor":
            1.00,

        "transactions_factor":
            1.00,

        "discount_factor":
            1.00,

        "cogs_factor":
            1.01,

        "description":
            (
                "Broadly stable control region."
            ),
    },
}


# ============================================================
# PRODUCT 10 GROWTH SCENARIO
# ============================================================

PRODUCT_10_GROSS_FACTOR = (
    1.08
)

PRODUCT_10_UNITS_FACTOR = (
    1.05
)

PRODUCT_10_TRANSACTIONS_FACTOR = (
    1.03
)

PRODUCT_10_COGS_FACTOR = (
    1.05
)


# ============================================================
# REQUIRED COLUMN CHECK
# ============================================================

def require_columns(
    dataframe: pd.DataFrame,
    columns: list[str],
) -> None:

    missing = [
        column
        for column
        in columns
        if (
            column
            not in
            dataframe.columns
        )
    ]

    if missing:

        raise RuntimeError(
            (
                "Required columns are missing from "
                "analytics.fact_sales_daily: "
                +
                ", ".join(
                    missing
                )
            )
        )


# ============================================================
# NUMERIC SERIES
# ============================================================

def numeric_series(
    dataframe: pd.DataFrame,
    column: str,
) -> pd.Series:

    return (
        pd.to_numeric(
            dataframe[
                column
            ],
            errors="coerce",
        )
        .fillna(
            0.0
        )
        .astype(
            "float64"
        )
    )


# ============================================================
# PREPARE SCALABLE COLUMNS
#
# This is the main fix for the Pandas LossySetitemError.
# ============================================================

def prepare_scalable_columns(
    dataframe: pd.DataFrame,
) -> None:

    print()
    print(
        "Preparing numeric columns for scenario scaling..."
    )

    for column in (
        SCALABLE_NUMERIC_COLUMNS
    ):

        if (
            column
            not in
            dataframe.columns
        ):

            continue

        original_dtype = (
            str(
                dataframe[
                    column
                ]
                .dtype
            )
        )

        dataframe[
            column
        ] = (
            pd.to_numeric(
                dataframe[
                    column
                ],
                errors="coerce",
            )
            .fillna(
                0.0
            )
            .astype(
                "float64"
            )
        )

        print(
            (
                f"  {column}: "
                f"{original_dtype} -> float64"
            )
        )


# ============================================================
# SCALE ONE COLUMN
# ============================================================

def scale_column(
    dataframe: pd.DataFrame,
    mask: pd.Series,
    column: str,
    factor: float,
) -> None:

    if (
        column
        not in
        dataframe.columns
    ):

        return

    if (
        not bool(
            mask.any()
        )
    ):

        return

    # --------------------------------------------------------
    # Defensive dtype conversion
    #
    # prepare_scalable_columns() should already have converted
    # these fields, but we repeat the safeguard here so that
    # this helper remains safe if used independently later.
    # --------------------------------------------------------

    if (
        not pd.api.types.is_float_dtype(
            dataframe[
                column
            ]
            .dtype
        )
    ):

        dataframe[
            column
        ] = (
            pd.to_numeric(
                dataframe[
                    column
                ],
                errors="coerce",
            )
            .fillna(
                0.0
            )
            .astype(
                "float64"
            )
        )

    dataframe.loc[
        mask,
        column,
    ] = (
        dataframe.loc[
            mask,
            column,
        ]
        *
        float(
            factor
        )
    )


# ============================================================
# DATE SHIFT
# ============================================================

def shift_july_date_to_august(
    value: Any,
) -> date:

    timestamp = (
        pd.Timestamp(
            value
        )
    )

    if (
        timestamp.year
        !=
        2026
        or
        timestamp.month
        !=
        7
    ):

        raise ValueError(
            (
                "Expected July 2026 date but found "
                f"{timestamp.date()}."
            )
        )

    return date(
        2026,
        8,
        timestamp.day,
    )


# ============================================================
# ROUND FINANCIAL COLUMNS
# ============================================================

def round_financial_columns(
    dataframe: pd.DataFrame,
) -> None:

    for column in (
        GROSS_SALES_COLUMN,
        DISCOUNT_COLUMN,
        NET_SALES_COLUMN,
        COGS_COLUMN,
    ):

        if (
            column
            not in
            dataframe.columns
        ):

            continue

        dataframe[
            column
        ] = (
            pd.to_numeric(
                dataframe[
                    column
                ],
                errors="coerce",
            )
            .fillna(
                0.0
            )
            .round(
                2
            )
            .astype(
                "float64"
            )
        )


# ============================================================
# ROUND INTEGER COLUMNS
#
# These measures may temporarily contain decimal values after
# scenario scaling.
#
# They are returned to integer business measures only after
# every scenario transformation is complete.
# ============================================================

def round_integer_columns(
    dataframe: pd.DataFrame,
) -> None:

    for column in (
        UNITS_COLUMN,
        TRANSACTIONS_COLUMN,
    ):

        if (
            column
            not in
            dataframe.columns
        ):

            continue

        dataframe[
            column
        ] = (
            pd.to_numeric(
                dataframe[
                    column
                ],
                errors="coerce",
            )
            .fillna(
                0.0
            )
            .round()
            .clip(
                lower=0
            )
            .astype(
                "int64"
            )
        )


# ============================================================
# MAINTAIN SALES IDENTITY
#
# net_sales = gross_sales - discount_amount
# ============================================================

def maintain_sales_identity(
    dataframe: pd.DataFrame,
) -> None:

    required = {
        GROSS_SALES_COLUMN,
        DISCOUNT_COLUMN,
        NET_SALES_COLUMN,
    }

    if (
        not required.issubset(
            dataframe.columns
        )
    ):

        return

    gross = (
        numeric_series(
            dataframe,
            GROSS_SALES_COLUMN,
        )
        .clip(
            lower=0
        )
    )

    discount = (
        numeric_series(
            dataframe,
            DISCOUNT_COLUMN,
        )
        .clip(
            lower=0
        )
    )

    # --------------------------------------------------------
    # Prevent synthetic discount from exceeding gross sales.
    # --------------------------------------------------------

    discount = (
        discount.where(
            discount
            <=
            gross,
            gross
            *
            0.95,
        )
    )

    dataframe[
        GROSS_SALES_COLUMN
    ] = gross

    dataframe[
        DISCOUNT_COLUMN
    ] = discount

    dataframe[
        NET_SALES_COLUMN
    ] = (
        gross
        -
        discount
    )


# ============================================================
# DATABASE PRIMARY KEY
# ============================================================

def get_primary_key_columns() -> list[str]:

    inspector = (
        inspect(
            engine
        )
    )

    pk = (
        inspector.get_pk_constraint(
            "fact_sales_daily",
            schema="analytics",
        )
    )

    return list(
        pk.get(
            "constrained_columns"
        )
        or
        []
    )


# ============================================================
# LOAD JULY SALES
# ============================================================

def load_july_sales() -> pd.DataFrame:

    query = text(
        """
        SELECT
            f.*,

            s.region
                AS __validation_region

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
                :start_date
                AND
                :end_date

        ORDER BY
            f.date_id,
            f.store_id,
            f.product_id;
        """
    )

    dataframe = (
        pd.read_sql_query(
            query,
            engine,
            params={
                "start_date":
                    SOURCE_START,

                "end_date":
                    SOURCE_END,
            },
        )
    )

    if dataframe.empty:

        raise RuntimeError(
            (
                "No July 2026 sales rows were found. "
                "August validation data cannot be generated."
            )
        )

    require_columns(
        dataframe,
        [
            DATE_COLUMN,
            STORE_COLUMN,
            PRODUCT_COLUMN,
            NET_SALES_COLUMN,
            UNITS_COLUMN,
        ],
    )

    return dataframe


# ============================================================
# REMOVE SURROGATE PRIMARY KEY
# ============================================================

def remove_surrogate_primary_key(
    dataframe: pd.DataFrame,
) -> tuple[
    pd.DataFrame,
    list[str],
]:

    pk_columns = (
        get_primary_key_columns()
    )

    dropped: list[str] = []

    natural_key_candidates = {
        DATE_COLUMN,
        STORE_COLUMN,
        PRODUCT_COLUMN,
        SALESPERSON_COLUMN,
    }

    if (
        len(
            pk_columns
        )
        ==
        1
    ):

        pk_column = (
            pk_columns[
                0
            ]
        )

        if (
            pk_column
            not in
            natural_key_candidates

            and

            pk_column
            in
            dataframe.columns
        ):

            dataframe = (
                dataframe.drop(
                    columns=[
                        pk_column
                    ]
                )
            )

            dropped.append(
                pk_column
            )

    return (
        dataframe,
        dropped,
    )


# ============================================================
# APPLY REGIONAL SCENARIOS
# ============================================================

def apply_regional_scenarios(
    dataframe: pd.DataFrame,
) -> None:

    print()
    print(
        "Applying controlled regional scenarios..."
    )

    region_series = (
        dataframe[
            "__validation_region"
        ]
        .astype(
            str
        )
        .str.strip()
        .str.casefold()
    )

    for (
        region,
        scenario,
    ) in (
        REGIONAL_SCENARIOS.items()
    ):

        mask = (
            region_series
            ==
            region.casefold()
        )

        row_count = int(
            mask.sum()
        )

        if (
            row_count
            ==
            0
        ):

            print(
                (
                    "  WARNING: no July rows found "
                    f"for region '{region}'."
                )
            )

            continue

        print(
            (
                f"  {region}: "
                f"{row_count:,} rows"
            )
        )

        scale_column(
            dataframe,
            mask,
            GROSS_SALES_COLUMN,
            scenario[
                "gross_sales_factor"
            ],
        )

        scale_column(
            dataframe,
            mask,
            UNITS_COLUMN,
            scenario[
                "units_factor"
            ],
        )

        scale_column(
            dataframe,
            mask,
            TRANSACTIONS_COLUMN,
            scenario[
                "transactions_factor"
            ],
        )

        # ----------------------------------------------------
        # Discount scales with gross sales first, then gets
        # its scenario-specific relative adjustment.
        # ----------------------------------------------------

        scale_column(
            dataframe,
            mask,
            DISCOUNT_COLUMN,
            (
                scenario[
                    "gross_sales_factor"
                ]
                *
                scenario[
                    "discount_factor"
                ]
            ),
        )

        scale_column(
            dataframe,
            mask,
            COGS_COLUMN,
            scenario[
                "cogs_factor"
            ],
        )

        # ----------------------------------------------------
        # Fallback if gross_sales is not part of the source.
        # ----------------------------------------------------

        if (
            GROSS_SALES_COLUMN
            not in
            dataframe.columns

            and

            NET_SALES_COLUMN
            in
            dataframe.columns
        ):

            scale_column(
                dataframe,
                mask,
                NET_SALES_COLUMN,
                scenario[
                    "gross_sales_factor"
                ],
            )


# ============================================================
# APPLY PRODUCT 10 GROWTH
# ============================================================

def apply_product_10_growth(
    dataframe: pd.DataFrame,
) -> None:

    if (
        PRODUCT_COLUMN
        not in
        dataframe.columns
    ):

        return

    product_values = (
        pd.to_numeric(
            dataframe[
                PRODUCT_COLUMN
            ],
            errors="coerce",
        )
    )

    mask = (
        product_values
        ==
        10
    )

    row_count = int(
        mask.sum()
    )

    print()
    print(
        (
            "Applying Product 10 continuation "
            f"scenario: {row_count:,} rows"
        )
    )

    if (
        row_count
        ==
        0
    ):

        print(
            (
                "  WARNING: Product ID 10 was not "
                "present in July."
            )
        )

        return

    scale_column(
        dataframe,
        mask,
        GROSS_SALES_COLUMN,
        PRODUCT_10_GROSS_FACTOR,
    )

    scale_column(
        dataframe,
        mask,
        UNITS_COLUMN,
        PRODUCT_10_UNITS_FACTOR,
    )

    scale_column(
        dataframe,
        mask,
        TRANSACTIONS_COLUMN,
        PRODUCT_10_TRANSACTIONS_FACTOR,
    )

    scale_column(
        dataframe,
        mask,
        COGS_COLUMN,
        PRODUCT_10_COGS_FACTOR,
    )

    if (
        GROSS_SALES_COLUMN
        not in
        dataframe.columns

        and

        NET_SALES_COLUMN
        in
        dataframe.columns
    ):

        scale_column(
            dataframe,
            mask,
            NET_SALES_COLUMN,
            PRODUCT_10_GROSS_FACTOR,
        )


# ============================================================
# VALIDATE GENERATED DATA
# ============================================================

def validate_generated_data(
    dataframe: pd.DataFrame,
) -> None:

    print()
    print(
        "Validating generated August rows..."
    )

    require_columns(
        dataframe,
        [
            DATE_COLUMN,
            STORE_COLUMN,
            PRODUCT_COLUMN,
        ],
    )

    dates = (
        pd.to_datetime(
            dataframe[
                DATE_COLUMN
            ],
            errors="raise",
        )
    )

    minimum_date = (
        dates
        .min()
        .date()
    )

    maximum_date = (
        dates
        .max()
        .date()
    )

    if (
        minimum_date
        !=
        TARGET_START
    ):

        raise RuntimeError(
            (
                "Generated data does not begin "
                "on 2026-08-01. "
                f"Found {minimum_date}."
            )
        )

    if (
        maximum_date
        !=
        TARGET_END
    ):

        raise RuntimeError(
            (
                "Generated data does not end "
                "on 2026-08-31. "
                f"Found {maximum_date}."
            )
        )

    if (
        dataframe[
            DATE_COLUMN
        ]
        .isna()
        .any()
    ):

        raise RuntimeError(
            (
                "Generated data contains null dates."
            )
        )

    for column in (
        GROSS_SALES_COLUMN,
        DISCOUNT_COLUMN,
        NET_SALES_COLUMN,
        COGS_COLUMN,
        UNITS_COLUMN,
        TRANSACTIONS_COLUMN,
    ):

        if (
            column
            not in
            dataframe.columns
        ):

            continue

        numeric = (
            pd.to_numeric(
                dataframe[
                    column
                ],
                errors="coerce",
            )
        )

        if (
            bool(
                numeric
                .isna()
                .any()
            )
        ):

            raise RuntimeError(
                (
                    "Generated data contains "
                    f"non-numeric/null values in {column}."
                )
            )

        if (
            bool(
                (
                    numeric
                    <
                    0
                )
                .any()
            )
        ):

            raise RuntimeError(
                (
                    "Generated data contains "
                    f"negative values in {column}."
                )
            )

    # --------------------------------------------------------
    # Check sales identity after transformations.
    # --------------------------------------------------------

    identity_columns = {
        GROSS_SALES_COLUMN,
        DISCOUNT_COLUMN,
        NET_SALES_COLUMN,
    }

    if (
        identity_columns
        .issubset(
            dataframe.columns
        )
    ):

        calculated_net = (
            pd.to_numeric(
                dataframe[
                    GROSS_SALES_COLUMN
                ],
                errors="coerce",
            )
            -
            pd.to_numeric(
                dataframe[
                    DISCOUNT_COLUMN
                ],
                errors="coerce",
            )
        )

        stored_net = (
            pd.to_numeric(
                dataframe[
                    NET_SALES_COLUMN
                ],
                errors="coerce",
            )
        )

        maximum_difference = (
            (
                calculated_net
                -
                stored_net
            )
            .abs()
            .max()
        )

        if (
            maximum_difference
            >
            0.02
        ):

            raise RuntimeError(
                (
                    "Sales identity validation failed. "
                    "gross_sales - discount_amount does "
                    "not match net_sales."
                )
            )

    print(
        "Validation passed."
    )


# ============================================================
# REGIONAL SUMMARY
# ============================================================

def regional_summary(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:

    working = (
        dataframe.copy()
    )

    for column in (
        NET_SALES_COLUMN,
        GROSS_SALES_COLUMN,
        COGS_COLUMN,
        UNITS_COLUMN,
        TRANSACTIONS_COLUMN,
        DISCOUNT_COLUMN,
    ):

        if (
            column
            in
            working.columns
        ):

            working[
                column
            ] = (
                pd.to_numeric(
                    working[
                        column
                    ],
                    errors="coerce",
                )
                .fillna(
                    0.0
                )
            )

    aggregation: dict[str, str] = {}

    for column in (
        NET_SALES_COLUMN,
        GROSS_SALES_COLUMN,
        COGS_COLUMN,
        UNITS_COLUMN,
        TRANSACTIONS_COLUMN,
        DISCOUNT_COLUMN,
    ):

        if (
            column
            in
            working.columns
        ):

            aggregation[
                column
            ] = (
                "sum"
            )

    summary = (
        working
        .groupby(
            "__validation_region",
            as_index=False,
        )
        .agg(
            aggregation
        )
    )

    summary = (
        summary.rename(
            columns={
                "__validation_region":
                    "region"
            }
        )
    )

    if (
        NET_SALES_COLUMN
        in
        summary.columns

        and

        COGS_COLUMN
        in
        summary.columns
    ):

        summary[
            "gross_profit"
        ] = (
            summary[
                NET_SALES_COLUMN
            ]
            -
            summary[
                COGS_COLUMN
            ]
        )

        summary[
            "margin_pct"
        ] = (
            summary[
                "gross_profit"
            ]
            /
            summary[
                NET_SALES_COLUMN
            ]
            .replace(
                0,
                pd.NA,
            )
            *
            100
        )

    return summary


# ============================================================
# BUILD REGIONAL COMPARISON
# ============================================================

def regional_comparison(
    july_summary: pd.DataFrame,
    august_summary: pd.DataFrame,
) -> pd.DataFrame:

    july = (
        july_summary.copy()
    )

    august = (
        august_summary.copy()
    )

    july = (
        july.rename(
            columns={
                column:
                    (
                        column
                        if column
                        ==
                        "region"
                        else
                        f"july_{column}"
                    )

                for column
                in july.columns
            }
        )
    )

    august = (
        august.rename(
            columns={
                column:
                    (
                        column
                        if column
                        ==
                        "region"
                        else
                        f"august_{column}"
                    )

                for column
                in august.columns
            }
        )
    )

    comparison = (
        july.merge(
            august,
            on="region",
            how="outer",
        )
    )

    for metric in (
        NET_SALES_COLUMN,
        "gross_profit",
        UNITS_COLUMN,
        TRANSACTIONS_COLUMN,
        "margin_pct",
    ):

        july_column = (
            f"july_{metric}"
        )

        august_column = (
            f"august_{metric}"
        )

        if (
            july_column
            not in
            comparison.columns

            or

            august_column
            not in
            comparison.columns
        ):

            continue

        baseline = (
            pd.to_numeric(
                comparison[
                    july_column
                ],
                errors="coerce",
            )
        )

        current = (
            pd.to_numeric(
                comparison[
                    august_column
                ],
                errors="coerce",
            )
        )

        if (
            metric
            ==
            "margin_pct"
        ):

            comparison[
                "margin_change_pp"
            ] = (
                current
                -
                baseline
            )

        else:

            comparison[
                f"{metric}_change_pct"
            ] = (
                (
                    current
                    -
                    baseline
                )
                /
                baseline
                .abs()
                .replace(
                    0,
                    pd.NA,
                )
                *
                100
            )

    return comparison


# ============================================================
# SCENARIO MANIFEST
# ============================================================

def write_scenario_manifest(
    output_path: Path,
    july_rows: int,
    august_rows: int,
    dropped_columns: list[str],
) -> None:

    payload = {
        "scenario":
            (
                "August 2026 controlled "
                "portfolio validation"
            ),

        "source_period": {
            "start":
                SOURCE_START.isoformat(),

            "end":
                SOURCE_END.isoformat(),
        },

        "target_period": {
            "start":
                TARGET_START.isoformat(),

            "end":
                TARGET_END.isoformat(),
        },

        "july_rows":
            july_rows,

        "august_rows":
            august_rows,

        "dropped_surrogate_columns":
            dropped_columns,

        "regional_scenarios":
            REGIONAL_SCENARIOS,

        "product_10": {
            "gross_sales_factor":
                PRODUCT_10_GROSS_FACTOR,

            "units_factor":
                PRODUCT_10_UNITS_FACTOR,

            "transactions_factor":
                PRODUCT_10_TRANSACTIONS_FACTOR,

            "cogs_factor":
                PRODUCT_10_COGS_FACTOR,
        },

        "expected_business_behavior": {
            "South":
                (
                    "Profitability improves materially "
                    "relative to July."
                ),

            "East":
                (
                    "Sales weakness continues."
                ),

            "West":
                (
                    "A new material sales deterioration "
                    "appears."
                ),

            "North":
                (
                    "Growth continues at a more "
                    "moderate rate."
                ),

            "Product 10":
                (
                    "The existing growth opportunity "
                    "continues."
                ),
        },

        "important":
            (
                "This is deterministic synthetic "
                "validation data for portfolio testing. "
                "It is not production business data."
            ),
    }

    output_path.write_text(
        json.dumps(
            payload,
            indent=2,
        ),
        encoding="utf-8",
    )


# ============================================================
# GENERATE
# ============================================================

def generate(
    output_dir: Path,
) -> dict:

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    print()
    print(
        "="
        *
        72
    )

    print(
        "AUGUST 2026 SALES VALIDATION GENERATOR"
    )

    print(
        "="
        *
        72
    )

    # --------------------------------------------------------
    # LOAD JULY
    # --------------------------------------------------------

    print()
    print(
        "Loading July 2026 warehouse sales..."
    )

    july = (
        load_july_sales()
    )

    july_row_count = (
        len(
            july
        )
    )

    print(
        (
            "July rows loaded: "
            f"{july_row_count:,}"
        )
    )

    # --------------------------------------------------------
    # COPY JULY → AUGUST
    # --------------------------------------------------------

    august = (
        july.copy(
            deep=True
        )
    )

    # --------------------------------------------------------
    # FIX NUMERIC DTYPES BEFORE SCALING
    #
    # This must happen BEFORE any factor multiplication.
    # --------------------------------------------------------

    prepare_scalable_columns(
        august
    )

    # --------------------------------------------------------
    # SHIFT DATES
    # --------------------------------------------------------

    print()
    print(
        "Shifting July dates to August 2026..."
    )

    august[
        DATE_COLUMN
    ] = (
        august[
            DATE_COLUMN
        ]
        .apply(
            shift_july_date_to_august
        )
    )

    # --------------------------------------------------------
    # REMOVE SURROGATE PRIMARY KEY
    # --------------------------------------------------------

    (
        august,
        dropped_columns,
    ) = (
        remove_surrogate_primary_key(
            august
        )
    )

    if dropped_columns:

        print()
        print(
            (
                "Dropped surrogate key columns "
                "from export:"
            )
        )

        for column in (
            dropped_columns
        ):

            print(
                f"  {column}"
            )

    # --------------------------------------------------------
    # APPLY REGIONAL CHANGES
    # --------------------------------------------------------

    apply_regional_scenarios(
        august
    )

    # --------------------------------------------------------
    # APPLY PRODUCT 10 CHANGE
    # --------------------------------------------------------

    apply_product_10_growth(
        august
    )

    # --------------------------------------------------------
    # RESTORE FINANCIAL IDENTITY
    # --------------------------------------------------------

    maintain_sales_identity(
        august
    )

    # --------------------------------------------------------
    # FINAL TYPE NORMALIZATION
    # --------------------------------------------------------

    round_financial_columns(
        august
    )

    round_integer_columns(
        august
    )

    # Recalculate identity once after rounding gross/discount.

    maintain_sales_identity(
        august
    )

    round_financial_columns(
        august
    )

    # --------------------------------------------------------
    # VALIDATE
    # --------------------------------------------------------

    validate_generated_data(
        august
    )

    # --------------------------------------------------------
    # SUMMARIES
    # --------------------------------------------------------

    print()
    print(
        "Building July / August regional summaries..."
    )

    july_summary = (
        regional_summary(
            july
        )
    )

    august_summary = (
        regional_summary(
            august
        )
    )

    comparison = (
        regional_comparison(
            july_summary,
            august_summary,
        )
    )

    # --------------------------------------------------------
    # REMOVE INTERNAL VALIDATION COLUMN
    # --------------------------------------------------------

    export_frame = (
        august.drop(
            columns=[
                "__validation_region"
            ],
            errors="ignore",
        )
    )

    # --------------------------------------------------------
    # OUTPUT PATHS
    # --------------------------------------------------------

    csv_path = (
        output_dir
        /
        "august_2026_sales_append.csv"
    )

    july_summary_path = (
        output_dir
        /
        "july_2026_regional_baseline.csv"
    )

    august_summary_path = (
        output_dir
        /
        "august_2026_regional_expected.csv"
    )

    comparison_path = (
        output_dir
        /
        "july_vs_august_2026_regional_comparison.csv"
    )

    manifest_path = (
        output_dir
        /
        "august_2026_validation_manifest.json"
    )

    # --------------------------------------------------------
    # WRITE OUTPUTS
    # --------------------------------------------------------

    export_frame.to_csv(
        csv_path,
        index=False,
        encoding="utf-8-sig",
    )

    july_summary.to_csv(
        july_summary_path,
        index=False,
        encoding="utf-8-sig",
    )

    august_summary.to_csv(
        august_summary_path,
        index=False,
        encoding="utf-8-sig",
    )

    comparison.to_csv(
        comparison_path,
        index=False,
        encoding="utf-8-sig",
    )

    write_scenario_manifest(
        manifest_path,
        july_rows=
            july_row_count,

        august_rows=
            len(
                export_frame
            ),

        dropped_columns=
            dropped_columns,
    )

    # --------------------------------------------------------
    # SUCCESS
    # --------------------------------------------------------

    print()
    print(
        "="
        *
        72
    )

    print(
        "GENERATION COMPLETE"
    )

    print(
        "="
        *
        72
    )

    print()
    print(
        (
            f"August rows generated: "
            f"{len(export_frame):,}"
        )
    )

    print()
    print(
        f"August source:"
    )
    print(
        f"  {csv_path}"
    )

    print()
    print(
        f"July regional baseline:"
    )
    print(
        f"  {july_summary_path}"
    )

    print()
    print(
        f"August expected regional summary:"
    )
    print(
        f"  {august_summary_path}"
    )

    print()
    print(
        f"July vs August comparison:"
    )
    print(
        f"  {comparison_path}"
    )

    print()
    print(
        f"Scenario manifest:"
    )
    print(
        f"  {manifest_path}"
    )

    print()
    print(
        (
            "No PostgreSQL rows were modified "
            "by this generator."
        )
    )

    return {
        "sales_csv":
            str(
                csv_path
            ),

        "july_summary":
            str(
                july_summary_path
            ),

        "august_summary":
            str(
                august_summary_path
            ),

        "comparison":
            str(
                comparison_path
            ),

        "manifest":
            str(
                manifest_path
            ),

        "rows":
            len(
                export_frame
            ),
    }


# ============================================================
# CLI
# ============================================================

def build_parser() -> argparse.ArgumentParser:

    parser = argparse.ArgumentParser(
        description=(
            "Generate controlled August 2026 "
            "sales records from the July "
            "warehouse baseline."
        )
    )

    parser.add_argument(
        "--output-dir",
        default=str(
            DEFAULT_OUTPUT_DIR
        ),
        help=(
            "Directory for generated "
            "validation files."
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

    output_dir = (
        Path(
            args.output_dir
        )
        .resolve()
    )

    generate(
        output_dir
    )

    return 0


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    raise SystemExit(
        main()
    )