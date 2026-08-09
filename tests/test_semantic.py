import pandas as pd

from backend.app.semantic.mapper import (
    canonicalize_dataframe,
    map_profile_to_canonical,
)

from backend.app.semantic.profiler import (
    normalize_header,
    profile_dataset,
)


# ============================================================
# HEADER NORMALIZATION
# ============================================================

def test_header_normalization():

    assert (
        normalize_header(
            " Net Sales ($) "
        )
        ==
        "net_sales"
    )


    assert (
        normalize_header(
            "SALES-QTY"
        )
        ==
        "sales_qty"
    )


    assert (
        normalize_header(
            "Territory Name"
        )
        ==
        "territory_name"
    )


# ============================================================
# SALES ALIAS MAPPING
# ============================================================

def test_common_sales_headers_map_correctly():

    rows = [

        {
            "Transaction Date":
                "2026-07-01",

            "Outlet Code":
                "OUT001",

            "SKU Description":
                "Energy Drink 250ml",

            "Sales Qty":
                20,

            "Sales Amount":
                50.0,

            "Product Cost":
                27.0,

            "Territory Name":
                "North",

            "Product Group":
                "Beverages",
        },

        {
            "Transaction Date":
                "2026-07-02",

            "Outlet Code":
                "OUT002",

            "SKU Description":
                "Cola 330ml",

            "Sales Qty":
                15,

            "Sales Amount":
                21.0,

            "Product Cost":
                10.5,

            "Territory Name":
                "West",

            "Product Group":
                "Beverages",
        },
    ]


    columns = list(
        rows[0].keys()
    )


    profile = (
        profile_dataset(
            columns,
            rows,
        )
    )


    result = (
        map_profile_to_canonical(
            profile
        )
    )


    mapping_lookup = {

        item[
            "source_column"
        ]:
            item[
                "canonical_field"
            ]

        for item
        in result[
            "mappings"
        ]
    }


    assert (
        mapping_lookup[
            "Transaction Date"
        ]
        ==
        "date"
    )

    assert (
        mapping_lookup[
            "Outlet Code"
        ]
        ==
        "store_id"
    )

    assert (
        mapping_lookup[
            "SKU Description"
        ]
        ==
        "product"
    )

    assert (
        mapping_lookup[
            "Sales Qty"
        ]
        ==
        "units_sold"
    )

    assert (
        mapping_lookup[
            "Sales Amount"
        ]
        ==
        "net_sales"
    )

    assert (
        mapping_lookup[
            "Product Cost"
        ]
        ==
        "cogs"
    )

    assert (
        mapping_lookup[
            "Territory Name"
        ]
        ==
        "region"
    )

    assert (
        mapping_lookup[
            "Product Group"
        ]
        ==
        "category"
    )


# ============================================================
# CAPABILITY DETECTION
# ============================================================

def test_capabilities_detected_from_available_fields():

    rows = [

        {
            "Date":
                "2026-07-01",

            "Revenue":
                500,

            "Quantity":
                100,

            "Cost":
                300,

            "Region":
                "North",
        }
    ]


    profile = (
        profile_dataset(
            list(
                rows[0].keys()
            ),
            rows,
        )
    )


    result = (
        map_profile_to_canonical(
            profile
        )
    )


    capabilities = (
        result[
            "strict_capabilities"
        ]
    )


    assert (
        "net_sales"
        in capabilities[
            "available_metrics"
        ]
    )

    assert (
        "gross_profit"
        in capabilities[
            "available_metrics"
        ]
    )

    assert (
        "margin_pct"
        in capabilities[
            "available_metrics"
        ]
    )

    assert (
        "avg_selling_price"
        in capabilities[
            "available_metrics"
        ]
    )

    assert (
        "region"
        in capabilities[
            "available_dimensions"
        ]
    )

    assert (
        "stockout_rate"
        not in capabilities[
            "available_metrics"
        ]
    )


# ============================================================
# UNKNOWN FIELD
# ============================================================

def test_unknown_field_not_forced_into_schema():

    rows = [

        {
            "ZXQ Mystery Field":
                "Something"
        }
    ]


    profile = (
        profile_dataset(
            list(
                rows[0].keys()
            ),
            rows,
        )
    )


    result = (
        map_profile_to_canonical(
            profile
        )
    )


    mapping = (
        result[
            "mappings"
        ][0]
    )


    assert (
        mapping[
            "status"
        ]
        ==
        "unresolved"
    )


    assert (
        mapping[
            "canonical_field"
        ]
        is None
    )


# ============================================================
# DATAFRAME CANONICALIZATION
# ============================================================

def test_dataframe_can_be_renamed_to_canonical_schema():

    dataframe = pd.DataFrame(
        [
            {
                "Transaction Date":
                    "2026-07-01",

                "Territory":
                    "North",

                "Revenue":
                    100.0,

                "Sales Qty":
                    20,
            }
        ]
    )


    profile = (
        profile_dataset(
            list(
                dataframe.columns
            ),
            dataframe.to_dict(
                "records"
            ),
        )
    )


    mapping_result = (
        map_profile_to_canonical(
            profile
        )
    )


    canonical = (
        canonicalize_dataframe(
            dataframe,
            mapping_result,
        )
    )


    assert (
        "date"
        in canonical.columns
    )

    assert (
        "region"
        in canonical.columns
    )

    assert (
        "net_sales"
        in canonical.columns
    )

    assert (
        "units_sold"
        in canonical.columns
    )