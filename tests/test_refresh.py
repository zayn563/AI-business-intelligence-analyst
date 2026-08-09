import pandas as pd
import pytest

from backend.app.ingestion.hasher import (
    add_record_identity,
)

from backend.app.ingestion.transformer import (
    apply_refresh_mapping_overrides,
    required_mapping_gaps,
    transform_to_sales_fact,
)

from backend.app.ingestion.validator import (
    validate_sales_fact_dataframe,
)

from backend.app.semantic.mapper import (
    map_profile_to_canonical,
)

from backend.app.semantic.profiler import (
    profile_dataset,
)

from backend.app.sources.schema_checker import (
    schema_fingerprint,
)


# ============================================================
# SAMPLE SALES FACT
# ============================================================

def sample_dataframe():

    return pd.DataFrame(
        [
            {
                "date_id":
                    "2026-07-01",

                "store_id":
                    1,

                "product_id":
                    1,

                "salesperson_id":
                    1,

                "units_sold":
                    20,

                "transactions":
                    10,

                "gross_sales":
                    50.00,

                "discount_amount":
                    1.00,

                "net_sales":
                    49.00,

                "cogs":
                    27.00,

                "returns_value":
                    0.00,

                "promo_flag":
                    False,
            }
        ]
    )


# ============================================================
# FINGERPRINT IS ORDER-INDEPENDENT
# ============================================================

def test_schema_fingerprint_ignores_column_order():

    one = schema_fingerprint(
        [
            "Revenue",
            "Date",
            "Region",
        ]
    )

    two = schema_fingerprint(
        [
            "Region",
            "Revenue",
            "Date",
        ]
    )


    assert one == two


# ============================================================
# HEADER CHANGE CHANGES FINGERPRINT
# ============================================================

def test_schema_fingerprint_detects_header_change():

    one = schema_fingerprint(
        [
            "Revenue",
            "Date",
        ]
    )

    two = schema_fingerprint(
        [
            "Net Sales",
            "Date",
        ]
    )


    assert one != two


# ============================================================
# CURRENT FACT HEADERS CAN BE MAPPED
# ============================================================

def test_current_fact_headers_transform():

    dataframe = sample_dataframe()


    profile = profile_dataset(

        columns=list(
            dataframe.columns
        ),

        sample_rows=(
            dataframe
            .to_dict(
                "records"
            )
        ),
    )


    mapping = (
        map_profile_to_canonical(
            profile
        )
    )


    mapping = (
        apply_refresh_mapping_overrides(
            mapping
        )
    )


    gaps = required_mapping_gaps(
        mapping[
            "mappings"
        ]
    )


    assert gaps == []


    transformed = (
        transform_to_sales_fact(

            dataframe,

            mapping[
                "mappings"
            ],
        )
    )


    assert (
        "date_id"
        in transformed.columns
    )


    assert (
        transformed.iloc[0][
            "net_sales"
        ]
        == 49.00
    )


# ============================================================
# HASH IS STABLE
# ============================================================

def test_record_hash_is_stable():

    dataframe = sample_dataframe()


    first = (
        add_record_identity(
            dataframe
        )
    )


    second = (
        add_record_identity(
            dataframe.copy()
        )
    )


    assert (
        first.iloc[0][
            "source_record_hash"
        ]
        ==
        second.iloc[0][
            "source_record_hash"
        ]
    )


# ============================================================
# CHANGING DATA CHANGES HASH
# ============================================================

def test_record_hash_changes_when_record_changes():

    original = sample_dataframe()


    changed = sample_dataframe()

    changed.loc[
        0,
        "net_sales",
    ] = 60.00


    first = (
        add_record_identity(
            original
        )
    )


    second = (
        add_record_identity(
            changed
        )
    )


    assert (
        first.iloc[0][
            "source_record_hash"
        ]
        !=
        second.iloc[0][
            "source_record_hash"
        ]
    )


# ============================================================
# DUPLICATE BUSINESS KEYS ARE REJECTED
# ============================================================

def test_duplicate_business_key_rejected():

    dataframe = sample_dataframe()


    dataframe = pd.concat(
        [
            dataframe,
            dataframe,
        ],
        ignore_index=True,
    )


    with pytest.raises(
        ValueError,
        match="Duplicate business keys",
    ):

        validate_sales_fact_dataframe(
            dataframe
        )