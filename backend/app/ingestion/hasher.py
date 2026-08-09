import hashlib

import pandas as pd


# ============================================================
# RECORD IDENTITY
# ============================================================

BUSINESS_KEY_FIELDS = [

    "date_id",

    "store_id",

    "product_id",
]


HASH_FIELDS = [

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
# NORMALIZED TEXT SERIES
# ============================================================

def _text_series(
    series: pd.Series,
) -> pd.Series:

    return (
        series
        .fillna("")
        .astype(str)
        .str.strip()
    )


# ============================================================
# ADD RECORD KEY + HASH
# ============================================================

def add_record_identity(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:

    result = dataframe.copy()


    # --------------------------------------------------------
    # BUSINESS KEY
    # --------------------------------------------------------

    key_series = (
        _text_series(
            result[
                BUSINESS_KEY_FIELDS[0]
            ]
        )
    )


    for field in (
        BUSINESS_KEY_FIELDS[1:]
    ):

        key_series = (
            key_series
            + "|"
            + _text_series(
                result[
                    field
                ]
            )
        )


    result[
        "source_record_key"
    ] = key_series


    # --------------------------------------------------------
    # ROW CONTENT HASH
    # --------------------------------------------------------

    payload = pd.Series(
        "",
        index=result.index,
        dtype="string",
    )


    for field in HASH_FIELDS:

        payload = (
            payload
            + "|"
            + _text_series(
                result[
                    field
                ]
            )
        )


    result[
        "source_record_hash"
    ] = payload.map(
        lambda value:
            hashlib.sha256(
                value.encode(
                    "utf-8"
                )
            ).hexdigest()
    )


    return result