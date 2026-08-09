import re
from typing import Any

import pandas as pd


# ============================================================
# HEADER NORMALIZATION
# ============================================================

def normalize_header(
    header: str,
) -> str:

    text = str(
        header
    ).strip().lower()


    # Convert symbols / spaces to underscores.
    text = re.sub(
        r"[^a-z0-9]+",
        "_",
        text,
    )


    # Collapse repeated underscores.
    text = re.sub(
        r"_+",
        "_",
        text,
    )


    return text.strip(
        "_"
    )


# ============================================================
# MISSING VALUE CHECK
# ============================================================

def _is_missing(
    value: Any,
) -> bool:

    if value is None:
        return True


    if isinstance(
        value,
        str,
    ):

        if not value.strip():
            return True


    try:

        missing = pd.isna(
            value
        )

        if isinstance(
            missing,
            bool,
        ):

            return missing

    except Exception:
        pass


    return False


# ============================================================
# TYPE HELPERS
# ============================================================

def _looks_like_identifier(
    normalized_header: str,
) -> bool:

    tokens = set(
        normalized_header.split(
            "_"
        )
    )


    identifier_tokens = {
        "id",
        "code",
        "sku",
        "key",
        "number",
        "no",
    }


    return bool(
        tokens
        & identifier_tokens
    )


def _looks_like_date_header(
    normalized_header: str,
) -> bool:

    tokens = set(
        normalized_header.split(
            "_"
        )
    )


    date_tokens = {
        "date",
        "day",
        "month",
        "year",
        "period",
        "time",
    }


    return bool(
        tokens
        & date_tokens
    )


def _date_string_ratio(
    values: list[Any],
) -> float:

    if not values:
        return 0.0


    matches = 0


    for value in values:

        text = str(
            value
        ).strip()


        # Common YYYY-MM-DD or YYYY/MM/DD style.
        if re.search(
            r"\d{4}[-/]\d{1,2}[-/]\d{1,2}",
            text,
        ):
            matches += 1


    return (
        matches
        / len(values)
    )


# ============================================================
# TYPE INFERENCE
# ============================================================

def infer_data_type(
    header: str,
    values: list[Any],
) -> str:

    normalized_header = (
        normalize_header(
            header
        )
    )


    clean_values = [

        value

        for value in values

        if not _is_missing(
            value
        )
    ]


    if not clean_values:

        return "unknown"


    # --------------------------------------------------------
    # Boolean
    # --------------------------------------------------------

    bool_strings = {
        "true",
        "false",
        "yes",
        "no",
        "y",
        "n",
    }


    if all(
        isinstance(
            value,
            bool,
        )

        for value in clean_values
    ):

        return "boolean"


    if all(
        str(value)
        .strip()
        .lower()
        in bool_strings

        for value in clean_values
    ):

        return "boolean"


    # --------------------------------------------------------
    # Identifiers
    #
    # Header semantics take precedence because numeric IDs
    # should not be treated as business measures.
    # --------------------------------------------------------

    if _looks_like_identifier(
        normalized_header
    ):

        return "identifier"


    # --------------------------------------------------------
    # Dates
    # --------------------------------------------------------

    date_hint = (
        _looks_like_date_header(
            normalized_header
        )
    )


    date_text_ratio = (
        _date_string_ratio(
            clean_values
        )
    )


    if (
        date_hint
        or date_text_ratio >= 0.80
    ):

        parsed_dates = (
            pd.to_datetime(
                pd.Series(
                    clean_values
                ),
                errors="coerce",
            )
        )


        valid_ratio = (
            parsed_dates
            .notna()
            .mean()
        )


        if valid_ratio >= 0.80:

            return "date"


    # --------------------------------------------------------
    # Numeric
    # --------------------------------------------------------

    numeric_values = (
        pd.to_numeric(
            pd.Series(
                clean_values
            ),
            errors="coerce",
        )
    )


    numeric_ratio = (
        numeric_values
        .notna()
        .mean()
    )


    if numeric_ratio >= 0.80:

        valid_numeric = (
            numeric_values
            .dropna()
        )


        if not valid_numeric.empty:

            integer_like = all(

                float(value)
                .is_integer()

                for value
                in valid_numeric
            )


            if integer_like:

                return "integer"


        return "numeric"


    # --------------------------------------------------------
    # Default
    # --------------------------------------------------------

    return "categorical"


# ============================================================
# COLUMN PROFILE
# ============================================================

def profile_column(
    column: str,
    sample_rows: list[dict],
    max_sample_values: int = 5,
) -> dict:

    raw_values = [

        row.get(
            column
        )

        for row
        in sample_rows
    ]


    clean_values = [

        value

        for value
        in raw_values

        if not _is_missing(
            value
        )
    ]


    inferred_type = (
        infer_data_type(
            column,
            clean_values,
        )
    )


    # --------------------------------------------------------
    # Samples
    # --------------------------------------------------------

    sample_values = []


    for value in clean_values:

        if value not in sample_values:

            sample_values.append(
                value
            )


        if (
            len(sample_values)
            >= max_sample_values
        ):
            break


    # --------------------------------------------------------
    # Uniqueness
    # --------------------------------------------------------

    unique_ratio = None


    if clean_values:

        unique_count = len(
            {
                str(value)
                for value
                in clean_values
            }
        )


        unique_ratio = round(
            unique_count
            / len(clean_values),
            4,
        )


    return {

        "source_column":
            column,

        "normalized_column":
            normalize_header(
                column
            ),

        "inferred_type":
            inferred_type,

        "sample_values":
            sample_values,

        "sample_non_null_count":
            len(
                clean_values
            ),

        "sample_unique_ratio":
            unique_ratio,
    }


# ============================================================
# DATASET PROFILE
# ============================================================

def profile_dataset(
    columns: list[str],
    sample_rows: list[dict],
    max_sample_values: int = 5,
) -> dict:

    profiles = [

        profile_column(
            column=column,
            sample_rows=sample_rows,
            max_sample_values=
                max_sample_values,
        )

        for column
        in columns
    ]


    return {

        "column_count":
            len(columns),

        "sample_row_count":
            len(sample_rows),

        "columns":
            profiles,
    }