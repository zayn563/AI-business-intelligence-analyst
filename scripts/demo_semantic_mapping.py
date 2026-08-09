from pathlib import Path
import sys

import pandas as pd


# ============================================================
# PROJECT IMPORT PATH
# ============================================================

ROOT = (
    Path(__file__)
    .resolve()
    .parents[1]
)


if str(
    ROOT
) not in sys.path:

    sys.path.insert(
        0,
        str(ROOT),
    )


from backend.app.semantic.mapper import (
    canonicalize_dataframe,
    map_profile_to_canonical,
)

from backend.app.semantic.profiler import (
    profile_dataset,
)


# ============================================================
# PATHS
# ============================================================

DATA_DIR = (
    ROOT
    / "data"
    / "generated"
)


# ============================================================
# LOAD A SMALL SAMPLE
# ============================================================

sales = pd.read_csv(

    DATA_DIR
    / "fact_sales_daily.csv",

    nrows=100,
)


stores = pd.read_csv(
    DATA_DIR
    / "dim_store.csv"
)


products = pd.read_csv(
    DATA_DIR
    / "dim_product.csv"
)


# ============================================================
# JOIN BUSINESS INFORMATION
# ============================================================

sample = (

    sales

    .merge(

        stores[
            [
                "store_id",
                "region",
                "city",
                "channel",
                "store_name",
            ]
        ],

        on="store_id",
        how="left",
    )

    .merge(

        products[
            [
                "product_id",
                "product_name",
                "brand",
                "category",
            ]
        ],

        on="product_id",
        how="left",
    )
)


# ============================================================
# SIMULATE A COMPLETELY DIFFERENT SALES FILE HEADER STRUCTURE
# ============================================================

variant = (

    sample[
        [
            "date_id",
            "store_id",
            "product_id",
            "units_sold",
            "transactions",
            "gross_sales",
            "discount_amount",
            "net_sales",
            "cogs",
            "returns_value",
            "promo_flag",
            "region",
            "city",
            "channel",
            "store_name",
            "product_name",
            "brand",
            "category",
        ]
    ]

    .rename(
        columns={

            "date_id":
                "Transaction Date",

            "store_id":
                "Outlet Code",

            "product_id":
                "SKU Code",

            "units_sold":
                "Sales Qty",

            "transactions":
                "Invoice Count",

            "gross_sales":
                "Gross Revenue",

            "discount_amount":
                "Discount Value",

            "net_sales":
                "Sales Amount",

            "cogs":
                "Product Cost",

            "returns_value":
                "Return Value",

            "promo_flag":
                "Promotion Flag",

            "region":
                "Territory Name",

            "city":
                "Market City",

            "channel":
                "Channel Type",

            "store_name":
                "Outlet Name",

            "product_name":
                "SKU Description",

            "brand":
                "Brand Name",

            "category":
                "Product Group",
        }
    )
)


# ============================================================
# PROFILE
# ============================================================

profile = (
    profile_dataset(

        columns=list(
            variant.columns
        ),

        sample_rows=(
            variant
            .head(50)
            .to_dict(
                "records"
            )
        ),
    )
)


# ============================================================
# MAP
# ============================================================

mapping = (
    map_profile_to_canonical(
        profile
    )
)


# ============================================================
# PRINT RESULTS
# ============================================================

print(
    "\n=============================================="
)

print(
    "SEMANTIC SALES SCHEMA DEMO"
)

print(
    "=============================================="
)


mapping_table = pd.DataFrame(

    mapping[
        "mappings"
    ]
)


print(
    "\nCOLUMN MAPPINGS\n"
)


print(

    mapping_table[
        [
            "source_column",
            "canonical_field",
            "confidence",
            "method",
            "status",
        ]
    ]

    .to_string(
        index=False
    )
)


print(
    "\nMAPPING SUMMARY\n"
)


for (
    key,
    value,
) in mapping[
    "summary"
].items():

    print(
        f"{key}: {value}"
    )


print(
    "\nSTRICT AVAILABLE METRICS\n"
)


print(

    mapping[
        "strict_capabilities"
    ][
        "available_metrics"
    ]
)


print(
    "\nSTRICT AVAILABLE DIMENSIONS\n"
)


print(

    mapping[
        "strict_capabilities"
    ][
        "available_dimensions"
    ]
)


print(
    "\nSTRICT AVAILABLE ANALYSES\n"
)


print(

    mapping[
        "strict_capabilities"
    ][
        "available_analyses"
    ]
)


# ============================================================
# CANONICALIZE THE DATAFRAME
# ============================================================

canonical = (
    canonicalize_dataframe(
        variant,
        mapping,
    )
)


print(
    "\nORIGINAL HEADERS\n"
)


print(
    list(
        variant.columns
    )
)


print(
    "\nCANONICALIZED HEADERS\n"
)


print(
    list(
        canonical.columns
    )
)


print(
    "\nCANONICAL SAMPLE\n"
)


print(
    canonical
    .head(3)
    .to_string(
        index=False
    )
)


print(
    "\n=============================================="
)

print(
    "DEMO COMPLETE"
)

print(
    "=============================================="
)