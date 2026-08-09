from copy import deepcopy

import pandas as pd


# ============================================================
# CURRENT SALES FACT CANONICAL REQUIREMENTS
#
# Canonical semantic "date" becomes warehouse "date_id".
# ============================================================

REQUIRED_CANONICAL_FIELDS = {

    "date",

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
}


# ============================================================
# REFRESH COMPATIBILITY OVERRIDES
#
# Our existing warehouse/export calls its date field "date_id",
# while the semantic layer calls the concept "date".
# ============================================================

def apply_refresh_mapping_overrides(
    mapping_result: dict,
) -> dict:

    result = deepcopy(
        mapping_result
    )


    for mapping in result[
        "mappings"
    ]:

        if (
            mapping[
                "normalized_column"
            ]
            == "date_id"
        ):

            mapping[
                "canonical_field"
            ] = "date"

            mapping[
                "expected_type"
            ] = "date"

            mapping[
                "confidence"
            ] = 1.0

            mapping[
                "method"
            ] = (
                "warehouse_compatibility"
            )

            mapping[
                "status"
            ] = (
                "auto_mapped"
            )


    return result


# ============================================================
# CHECK REQUIRED CANONICAL MAPPINGS
# ============================================================

def required_mapping_gaps(
    mappings: list[dict],
) -> list[str]:

    available = set()


    for mapping in mappings:

        status = (
            mapping.get(
                "status"
            )
            or mapping.get(
                "mapping_status"
            )
        )


        confirmed = mapping.get(
            "is_confirmed",
            False,
        )


        if (
            mapping.get(
                "canonical_field"
            )
            is not None
            and (
                status
                == "auto_mapped"
                or confirmed
            )
        ):

            available.add(
                mapping[
                    "canonical_field"
                ]
            )


    return sorted(
        REQUIRED_CANONICAL_FIELDS
        - available
    )


# ============================================================
# BOOLEAN PARSING
# ============================================================

def _parse_boolean(
    value,
):

    if isinstance(
        value,
        bool,
    ):

        return value


    text = str(
        value
    ).strip().lower()


    if text in {
        "true",
        "1",
        "yes",
        "y",
    }:

        return True


    if text in {
        "false",
        "0",
        "no",
        "n",
    }:

        return False


    raise ValueError(
        f"Cannot interpret boolean value: "
        f"{value}"
    )


# ============================================================
# TRANSFORM TO CURRENT FACT TABLE FORMAT
# ============================================================

def transform_to_sales_fact(
    dataframe: pd.DataFrame,
    mappings: list[dict],
) -> pd.DataFrame:

    rename_map = {}

    used_targets = set()


    # Highest-confidence mappings first.
    mappings_sorted = sorted(

        mappings,

        key=lambda item:
            float(
                item.get(
                    "confidence"
                )
                or 0
            ),

        reverse=True,
    )


    for mapping in mappings_sorted:

        canonical_field = (
            mapping.get(
                "canonical_field"
            )
        )


        if canonical_field is None:
            continue


        status = (
            mapping.get(
                "status"
            )
            or mapping.get(
                "mapping_status"
            )
        )


        confirmed = mapping.get(
            "is_confirmed",
            False,
        )


        if (
            status
            != "auto_mapped"
            and not confirmed
        ):

            continue


        if canonical_field in used_targets:
            continue


        rename_map[
            mapping[
                "source_column"
            ]
        ] = canonical_field


        used_targets.add(
            canonical_field
        )


    transformed = dataframe.rename(
        columns=rename_map
    ).copy()


    # --------------------------------------------------------
    # Canonical date → warehouse date_id
    # --------------------------------------------------------

    if "date" in transformed.columns:

        transformed = transformed.rename(
            columns={
                "date":
                    "date_id"
            }
        )


    # --------------------------------------------------------
    # TYPE COERCION
    # --------------------------------------------------------

    transformed[
        "date_id"
    ] = (

        pd.to_datetime(
            transformed[
                "date_id"
            ],
            errors="coerce",
        )
        .dt.date
    )


    integer_fields = [

        "store_id",

        "product_id",

        "salesperson_id",

        "units_sold",

        "transactions",
    ]


    for field in integer_fields:

        transformed[
            field
        ] = pd.to_numeric(
            transformed[
                field
            ],
            errors="coerce",
        )


    decimal_fields = [

        "gross_sales",

        "discount_amount",

        "net_sales",

        "cogs",

        "returns_value",
    ]


    for field in decimal_fields:

        transformed[
            field
        ] = pd.to_numeric(
            transformed[
                field
            ],
            errors="coerce",
        )


    transformed[
        "promo_flag"
    ] = transformed[
        "promo_flag"
    ].map(
        _parse_boolean
    )


    output_columns = [

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


    return transformed[
        output_columns
    ].copy()