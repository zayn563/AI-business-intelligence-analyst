import pandas as pd

from ..semantic.profiler import (
    normalize_header,
)


# ============================================================
# REQUIRED FIELDS FOR CURRENT STAR-WAREHOUSE SALES FACT
# ============================================================

REQUIRED_FACT_FIELDS = [

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


BUSINESS_KEY_FIELDS = [

    "date_id",

    "store_id",

    "product_id",
]


NON_NEGATIVE_FIELDS = [

    "units_sold",

    "transactions",

    "gross_sales",

    "discount_amount",

    "net_sales",

    "cogs",

    "returns_value",
]


# ============================================================
# SOURCE-LEVEL VALIDATION
# ============================================================

def validate_source_dataframe(
    dataframe: pd.DataFrame,
):

    if dataframe.empty:

        raise ValueError(
            "Source dataset contains no rows."
        )


    if len(
        dataframe.columns
    ) == 0:

        raise ValueError(
            "Source dataset contains no columns."
        )


    if dataframe.columns.duplicated().any():

        duplicates = (
            dataframe.columns[
                dataframe.columns.duplicated()
            ]
            .tolist()
        )


        raise ValueError(
            f"Duplicate source columns found: "
            f"{duplicates}"
        )


    normalized_columns = [

        normalize_header(
            column
        )

        for column
        in dataframe.columns
    ]


    if (
        len(normalized_columns)
        != len(
            set(
                normalized_columns
            )
        )
    ):

        raise ValueError(
            "Two or more source headers become "
            "identical after normalization."
        )


# ============================================================
# CANONICAL FACT VALIDATION
# ============================================================

def validate_sales_fact_dataframe(
    dataframe: pd.DataFrame,
):

    missing = [

        field

        for field
        in REQUIRED_FACT_FIELDS

        if field
        not in dataframe.columns
    ]


    if missing:

        raise ValueError(
            "Required sales fields are missing: "
            f"{missing}"
        )


    # --------------------------------------------------------
    # NULL CHECK
    # --------------------------------------------------------

    null_counts = (

        dataframe[
            REQUIRED_FACT_FIELDS
        ]

        .isna()

        .sum()
    )


    null_problem = {

        column:
            int(count)

        for column, count
        in null_counts.items()

        if count > 0
    }


    if null_problem:

        raise ValueError(
            "Required fields contain null values: "
            f"{null_problem}"
        )


    # --------------------------------------------------------
    # BUSINESS KEY DUPLICATES
    # --------------------------------------------------------

    duplicate_mask = (
        dataframe.duplicated(
            subset=BUSINESS_KEY_FIELDS,
            keep=False,
        )
    )


    if duplicate_mask.any():

        duplicate_count = int(
            duplicate_mask.sum()
        )


        raise ValueError(
            "Duplicate business keys found in "
            f"source data: {duplicate_count} rows."
        )


    # --------------------------------------------------------
    # NON-NEGATIVE CHECKS
    # --------------------------------------------------------

    negative_counts = {}


    for field in NON_NEGATIVE_FIELDS:

        count = int(
            (
                dataframe[
                    field
                ]
                < 0
            )
            .sum()
        )


        if count:

            negative_counts[
                field
            ] = count


    if negative_counts:

        raise ValueError(
            "Negative values found in fields "
            "that must be non-negative: "
            f"{negative_counts}"
        )