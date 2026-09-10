from __future__ import annotations

import argparse
import calendar
import sys

from datetime import (
    date,
    datetime,
    timedelta,
)

from pathlib import Path
from typing import (
    Any,
    Callable,
)

from sqlalchemy import (
    MetaData,
    Table,
    inspect,
    select,
    text,
)

from sqlalchemy.sql.schema import Column


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
# CONSTANTS
# ============================================================

SCHEMA_NAME = (
    "analytics"
)

TABLE_NAME = (
    "dim_date"
)

DATE_COLUMN = (
    "date_id"
)

DEFAULT_THROUGH_DATE = (
    date(
        2026,
        8,
        31,
    )
)


# ============================================================
# TYPES
# ============================================================

CandidateFunction = Callable[
    [
        date,
    ],
    Any,
]


# ============================================================
# BASIC DATE HELPERS
# ============================================================

def month_start(
    value: date,
) -> date:

    return value.replace(
        day=1
    )


def month_end(
    value: date,
) -> date:

    last_day = (
        calendar.monthrange(
            value.year,
            value.month,
        )[1]
    )

    return value.replace(
        day=last_day
    )


def quarter_number(
    value: date,
) -> int:

    return (
        (
            value.month
            -
            1
        )
        //
        3
        +
        1
    )


def quarter_start(
    value: date,
) -> date:

    quarter = (
        quarter_number(
            value
        )
    )

    month = (
        (
            quarter
            -
            1
        )
        *
        3
        +
        1
    )

    return date(
        value.year,
        month,
        1,
    )


def quarter_end(
    value: date,
) -> date:

    start = (
        quarter_start(
            value
        )
    )

    end_month = (
        start.month
        +
        2
    )

    return month_end(
        date(
            start.year,
            end_month,
            1,
        )
    )


def year_start(
    value: date,
) -> date:

    return date(
        value.year,
        1,
        1,
    )


def year_end(
    value: date,
) -> date:

    return date(
        value.year,
        12,
        31,
    )


def monday_week_start(
    value: date,
) -> date:

    return (
        value
        -
        timedelta(
            days=
                value.weekday()
        )
    )


def sunday_week_start(
    value: date,
) -> date:

    postgres_dow = (
        (
            value.weekday()
            +
            1
        )
        %
        7
    )

    return (
        value
        -
        timedelta(
            days=
                postgres_dow
        )
    )


def monday_week_end(
    value: date,
) -> date:

    return (
        monday_week_start(
            value
        )
        +
        timedelta(
            days=6
        )
    )


def sunday_week_end(
    value: date,
) -> date:

    return (
        sunday_week_start(
            value
        )
        +
        timedelta(
            days=6
        )
    )


# ============================================================
# COLUMN NAME NORMALIZATION
# ============================================================

def normalize_column_name(
    value: str,
) -> str:

    return (
        str(value)
        .strip()
        .lower()
    )


# ============================================================
# VALUE NORMALIZATION FOR INFERENCE
# ============================================================

def normalize_value(
    value: Any,
) -> Any:

    if value is None:

        return None

    if isinstance(
        value,
        datetime,
    ):

        return value.date()

    if isinstance(
        value,
        date,
    ):

        return value

    if isinstance(
        value,
        bool,
    ):

        return bool(
            value
        )

    if isinstance(
        value,
        str,
    ):

        return (
            value
            .strip()
            .casefold()
        )

    try:

        if (
            hasattr(
                value,
                "item",
            )
        ):

            value = (
                value.item()
            )

    except Exception:

        pass

    return value


def values_equal(
    actual: Any,
    expected: Any,
) -> bool:

    actual_normalized = (
        normalize_value(
            actual
        )
    )

    expected_normalized = (
        normalize_value(
            expected
        )
    )

    if (
        isinstance(
            actual_normalized,
            bool,
        )
        and
        isinstance(
            expected_normalized,
            int,
        )
    ):

        return (
            int(
                actual_normalized
            )
            ==
            expected_normalized
        )

    if (
        isinstance(
            expected_normalized,
            bool,
        )
        and
        isinstance(
            actual_normalized,
            int,
        )
    ):

        return (
            actual_normalized
            ==
            int(
                expected_normalized
            )
        )

    return (
        actual_normalized
        ==
        expected_normalized
    )


# ============================================================
# CANDIDATE GENERATORS
#
# We infer the convention already used by the existing table.
#
# Example:
#
# day_of_week could be:
#   Monday = 0
#   Monday = 1
#   Sunday = 0
#
# Rather than guessing, the script compares candidates against
# existing dim_date rows and chooses the candidate that matches.
# ============================================================

def candidate_generators(
    column_name: str,
) -> list[
    tuple[
        str,
        CandidateFunction,
    ]
]:

    name = (
        normalize_column_name(
            column_name
        )
    )

    # --------------------------------------------------------
    # DATE
    # --------------------------------------------------------

    if name in {
        "date_id",
        "date",
        "full_date",
        "calendar_date",
    }:

        return [
            (
                "calendar_date",
                lambda value:
                    value,
            ),
        ]

    # --------------------------------------------------------
    # DATE KEY
    # --------------------------------------------------------

    if name in {
        "date_key",
        "datekey",
    }:

        return [
            (
                "yyyymmdd_integer",
                lambda value:
                    int(
                        value.strftime(
                            "%Y%m%d"
                        )
                    ),
            ),
            (
                "yyyymmdd_text",
                lambda value:
                    value.strftime(
                        "%Y%m%d"
                    ),
            ),
        ]

    # --------------------------------------------------------
    # YEAR
    # --------------------------------------------------------

    if name in {
        "year",
        "calendar_year",
        "year_num",
        "year_number",
    }:

        return [
            (
                "year_number",
                lambda value:
                    value.year,
            ),
            (
                "year_text",
                lambda value:
                    str(
                        value.year
                    ),
            ),
        ]

    # --------------------------------------------------------
    # MONTH NUMBER
    # --------------------------------------------------------

    if name in {
        "month",
        "month_num",
        "month_number",
        "calendar_month",
    }:

        return [
            (
                "month_number",
                lambda value:
                    value.month,
            ),
            (
                "month_zero_padded",
                lambda value:
                    f"{value.month:02d}",
            ),
            (
                "month_full_name",
                lambda value:
                    value.strftime(
                        "%B"
                    ),
            ),
            (
                "month_short_name",
                lambda value:
                    value.strftime(
                        "%b"
                    ),
            ),
        ]

    # --------------------------------------------------------
    # MONTH NAME
    # --------------------------------------------------------

    if name in {
        "month_name",
        "monthname",
    }:

        return [
            (
                "month_full_name",
                lambda value:
                    value.strftime(
                        "%B"
                    ),
            ),
            (
                "month_full_name_upper",
                lambda value:
                    value.strftime(
                        "%B"
                    )
                    .upper(),
            ),
            (
                "month_full_name_lower",
                lambda value:
                    value.strftime(
                        "%B"
                    )
                    .lower(),
            ),
            (
                "month_short_name",
                lambda value:
                    value.strftime(
                        "%b"
                    ),
            ),
        ]

    # --------------------------------------------------------
    # MONTH ABBREVIATION
    # --------------------------------------------------------

    if name in {
        "month_short_name",
        "month_abbr",
        "month_abbreviation",
    }:

        return [
            (
                "month_short_name",
                lambda value:
                    value.strftime(
                        "%b"
                    ),
            ),
            (
                "month_short_name_upper",
                lambda value:
                    value.strftime(
                        "%b"
                    )
                    .upper(),
            ),
            (
                "month_short_name_lower",
                lambda value:
                    value.strftime(
                        "%b"
                    )
                    .lower(),
            ),
        ]

    # --------------------------------------------------------
    # DAY OF MONTH
    # --------------------------------------------------------

    if name in {
        "day",
        "day_num",
        "day_number",
        "day_of_month",
    }:

        return [
            (
                "day_of_month",
                lambda value:
                    value.day,
            ),
            (
                "day_zero_padded",
                lambda value:
                    f"{value.day:02d}",
            ),
        ]

    # --------------------------------------------------------
    # DAY OF YEAR
    # --------------------------------------------------------

    if name in {
        "day_of_year",
        "dayofyear",
    }:

        return [
            (
                "day_of_year",
                lambda value:
                    int(
                        value.strftime(
                            "%j"
                        )
                    ),
            ),
        ]

    # --------------------------------------------------------
    # DAY OF WEEK
    # --------------------------------------------------------

    if name in {
        "day_of_week",
        "weekday",
        "weekday_num",
        "weekday_number",
        "dow",
    }:

        return [
            (
                "monday_zero",
                lambda value:
                    value.weekday(),
            ),
            (
                "monday_one",
                lambda value:
                    value.isoweekday(),
            ),
            (
                "sunday_zero",
                lambda value:
                    (
                        value.weekday()
                        +
                        1
                    )
                    %
                    7,
            ),
            (
                "weekday_full_name",
                lambda value:
                    value.strftime(
                        "%A"
                    ),
            ),
            (
                "weekday_short_name",
                lambda value:
                    value.strftime(
                        "%a"
                    ),
            ),
        ]

    # --------------------------------------------------------
    # ISO DAY OF WEEK
    # --------------------------------------------------------

    if name in {
        "iso_day_of_week",
        "iso_weekday",
    }:

        return [
            (
                "iso_weekday",
                lambda value:
                    value.isoweekday(),
            ),
        ]

    # --------------------------------------------------------
    # DAY NAME
    # --------------------------------------------------------

    if name in {
        "day_name",
        "weekday_name",
    }:

        return [
            (
                "weekday_full_name",
                lambda value:
                    value.strftime(
                        "%A"
                    ),
            ),
            (
                "weekday_full_name_upper",
                lambda value:
                    value.strftime(
                        "%A"
                    )
                    .upper(),
            ),
            (
                "weekday_full_name_lower",
                lambda value:
                    value.strftime(
                        "%A"
                    )
                    .lower(),
            ),
            (
                "weekday_short_name",
                lambda value:
                    value.strftime(
                        "%a"
                    ),
            ),
        ]

    # --------------------------------------------------------
    # DAY ABBREVIATION
    # --------------------------------------------------------

    if name in {
        "day_short_name",
        "day_abbr",
        "weekday_abbr",
    }:

        return [
            (
                "weekday_short_name",
                lambda value:
                    value.strftime(
                        "%a"
                    ),
            ),
            (
                "weekday_short_name_upper",
                lambda value:
                    value.strftime(
                        "%a"
                    )
                    .upper(),
            ),
            (
                "weekday_short_name_lower",
                lambda value:
                    value.strftime(
                        "%a"
                    )
                    .lower(),
            ),
        ]

    # --------------------------------------------------------
    # WEEK NUMBER
    # --------------------------------------------------------

    if name in {
        "week",
        "week_num",
        "week_number",
        "week_of_year",
        "iso_week",
    }:

        return [
            (
                "iso_week",
                lambda value:
                    value.isocalendar().week,
            ),
            (
                "sunday_week_number",
                lambda value:
                    int(
                        value.strftime(
                            "%U"
                        )
                    ),
            ),
            (
                "monday_week_number",
                lambda value:
                    int(
                        value.strftime(
                            "%W"
                        )
                    ),
            ),
        ]

    # --------------------------------------------------------
    # ISO YEAR
    # --------------------------------------------------------

    if name in {
        "iso_year",
    }:

        return [
            (
                "iso_year",
                lambda value:
                    value.isocalendar().year,
            ),
        ]

    # --------------------------------------------------------
    # QUARTER
    # --------------------------------------------------------

    if name in {
        "quarter",
        "quarter_num",
        "quarter_number",
    }:

        return [
            (
                "quarter_number",
                lambda value:
                    quarter_number(
                        value
                    ),
            ),
            (
                "quarter_label",
                lambda value:
                    (
                        f"Q"
                        f"{quarter_number(value)}"
                    ),
            ),
        ]

    # --------------------------------------------------------
    # QUARTER NAME / LABEL
    # --------------------------------------------------------

    if name in {
        "quarter_name",
        "quarter_label",
    }:

        return [
            (
                "quarter_label",
                lambda value:
                    (
                        f"Q"
                        f"{quarter_number(value)}"
                    ),
            ),
            (
                "quarter_number_text",
                lambda value:
                    str(
                        quarter_number(
                            value
                        )
                    ),
            ),
        ]

    # --------------------------------------------------------
    # YEAR-MONTH
    # --------------------------------------------------------

    if name in {
        "year_month",
        "yearmonth",
        "month_key",
    }:

        return [
            (
                "yyyymm_integer",
                lambda value:
                    (
                        value.year
                        *
                        100
                        +
                        value.month
                    ),
            ),
            (
                "yyyymm_text",
                lambda value:
                    value.strftime(
                        "%Y%m"
                    ),
            ),
            (
                "yyyy_mm_text",
                lambda value:
                    value.strftime(
                        "%Y-%m"
                    ),
            ),
            (
                "month_year_full",
                lambda value:
                    value.strftime(
                        "%B %Y"
                    ),
            ),
            (
                "month_year_short",
                lambda value:
                    value.strftime(
                        "%b %Y"
                    ),
            ),
        ]

    # --------------------------------------------------------
    # YEAR-QUARTER
    # --------------------------------------------------------

    if name in {
        "year_quarter",
        "yearquarter",
        "quarter_key",
    }:

        return [
            (
                "year_quarter_label",
                lambda value:
                    (
                        f"{value.year}-Q"
                        f"{quarter_number(value)}"
                    ),
            ),
            (
                "year_quarter_compact",
                lambda value:
                    (
                        f"{value.year}Q"
                        f"{quarter_number(value)}"
                    ),
            ),
        ]

    # --------------------------------------------------------
    # MONTH START / END
    # --------------------------------------------------------

    if name in {
        "month_start",
        "month_start_date",
        "first_day_of_month",
    }:

        return [
            (
                "month_start",
                lambda value:
                    month_start(
                        value
                    ),
            ),
        ]

    if name in {
        "month_end",
        "month_end_date",
        "last_day_of_month",
    }:

        return [
            (
                "month_end",
                lambda value:
                    month_end(
                        value
                    ),
            ),
        ]

    # --------------------------------------------------------
    # QUARTER START / END
    # --------------------------------------------------------

    if name in {
        "quarter_start",
        "quarter_start_date",
    }:

        return [
            (
                "quarter_start",
                lambda value:
                    quarter_start(
                        value
                    ),
            ),
        ]

    if name in {
        "quarter_end",
        "quarter_end_date",
    }:

        return [
            (
                "quarter_end",
                lambda value:
                    quarter_end(
                        value
                    ),
            ),
        ]

    # --------------------------------------------------------
    # YEAR START / END
    # --------------------------------------------------------

    if name in {
        "year_start",
        "year_start_date",
    }:

        return [
            (
                "year_start",
                lambda value:
                    year_start(
                        value
                    ),
            ),
        ]

    if name in {
        "year_end",
        "year_end_date",
    }:

        return [
            (
                "year_end",
                lambda value:
                    year_end(
                        value
                    ),
            ),
        ]

    # --------------------------------------------------------
    # WEEK START / END
    # --------------------------------------------------------

    if name in {
        "week_start",
        "week_start_date",
    }:

        return [
            (
                "monday_week_start",
                lambda value:
                    monday_week_start(
                        value
                    ),
            ),
            (
                "sunday_week_start",
                lambda value:
                    sunday_week_start(
                        value
                    ),
            ),
        ]

    if name in {
        "week_end",
        "week_end_date",
    }:

        return [
            (
                "monday_week_end",
                lambda value:
                    monday_week_end(
                        value
                    ),
            ),
            (
                "sunday_week_end",
                lambda value:
                    sunday_week_end(
                        value
                    ),
            ),
        ]

    # --------------------------------------------------------
    # WEEKEND / WEEKDAY FLAG
    # --------------------------------------------------------

    if name in {
        "is_weekend",
        "weekend_flag",
    }:

        return [
            (
                "weekend_boolean",
                lambda value:
                    (
                        value.weekday()
                        >=
                        5
                    ),
            ),
            (
                "weekend_integer",
                lambda value:
                    (
                        1
                        if
                        value.weekday()
                        >=
                        5
                        else
                        0
                    ),
            ),
            (
                "weekend_yes_no",
                lambda value:
                    (
                        "Yes"
                        if
                        value.weekday()
                        >=
                        5
                        else
                        "No"
                    ),
            ),
        ]

    if name in {
        "is_weekday",
        "weekday_flag",
    }:

        return [
            (
                "weekday_boolean",
                lambda value:
                    (
                        value.weekday()
                        <
                        5
                    ),
            ),
            (
                "weekday_integer",
                lambda value:
                    (
                        1
                        if
                        value.weekday()
                        <
                        5
                        else
                        0
                    ),
            ),
        ]

    return []


# ============================================================
# TABLE METADATA
# ============================================================

def reflect_date_table() -> Table:

    metadata = (
        MetaData()
    )

    return Table(
        TABLE_NAME,
        metadata,
        schema=
            SCHEMA_NAME,
        autoload_with=
            engine,
    )


def inspect_columns() -> list[dict]:

    inspector = (
        inspect(
            engine
        )
    )

    return (
        inspector.get_columns(
            TABLE_NAME,
            schema=
                SCHEMA_NAME,
        )
    )


# ============================================================
# DATE COVERAGE
# ============================================================

def get_date_coverage() -> dict:

    query = text(
        """
        SELECT
            COUNT(*)
                AS row_count,

            COUNT(
                DISTINCT date_id
            )
                AS distinct_dates,

            MIN(date_id)
                AS minimum_date,

            MAX(date_id)
                AS maximum_date

        FROM
            analytics.dim_date;
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
# LOAD SAMPLE ROWS
# ============================================================

def load_sample_rows(
    table: Table,
    sample_size: int = 60,
) -> list[dict]:

    statement = (
        select(
            table
        )
        .order_by(
            table.c[
                DATE_COLUMN
            ]
            .desc()
        )
        .limit(
            sample_size
        )
    )

    with engine.connect() as connection:

        rows = (
            connection
            .execute(
                statement
            )
            .mappings()
            .all()
        )

    return [
        dict(
            row
        )
        for row
        in rows
    ]


# ============================================================
# INFER ONE COLUMN GENERATOR
# ============================================================

def infer_generator(
    column_name: str,
    sample_rows: list[dict],
) -> tuple[
    str,
    CandidateFunction,
] | None:

    candidates = (
        candidate_generators(
            column_name
        )
    )

    if not candidates:

        return None

    if (
        column_name
        ==
        DATE_COLUMN
    ):

        return (
            candidates[
                0
            ]
        )

    matching_candidates: list[
        tuple[
            str,
            CandidateFunction,
        ]
    ] = []

    for (
        candidate_name,
        candidate_function,
    ) in candidates:

        candidate_matches = True

        rows_checked = 0

        for row in sample_rows:

            source_date = (
                row.get(
                    DATE_COLUMN
                )
            )

            actual_value = (
                row.get(
                    column_name
                )
            )

            if (
                source_date is None
                or
                actual_value is None
            ):

                continue

            if isinstance(
                source_date,
                datetime,
            ):

                source_date = (
                    source_date.date()
                )

            expected_value = (
                candidate_function(
                    source_date
                )
            )

            rows_checked += 1

            if not values_equal(
                actual_value,
                expected_value,
            ):

                candidate_matches = False
                break

        if (
            candidate_matches
            and
            rows_checked
            >
            0
        ):

            matching_candidates.append(
                (
                    candidate_name,
                    candidate_function,
                )
            )

    if not matching_candidates:

        return None

    return (
        matching_candidates[
            0
        ]
    )


# ============================================================
# REQUIRED COLUMN CHECK
# ============================================================

def column_can_be_omitted(
    column: Column,
) -> bool:

    if column.nullable:

        return True

    if (
        column.default
        is not None
    ):

        return True

    if (
        column.server_default
        is not None
    ):

        return True

    if (
        column.autoincrement
        is True
    ):

        return True

    return False


# ============================================================
# BUILD GENERATOR MAP
# ============================================================

def build_generator_map(
    table: Table,
    sample_rows: list[dict],
) -> dict[
    str,
    tuple[
        str,
        CandidateFunction,
    ],
]:

    if (
        DATE_COLUMN
        not in
        table.c
    ):

        raise RuntimeError(
            (
                "analytics.dim_date does not contain "
                "the required date_id column."
            )
        )

    generator_map: dict[
        str,
        tuple[
            str,
            CandidateFunction,
        ],
    ] = {}

    unsupported_required: list[str] = []

    for column in table.columns:

        column_name = (
            column.name
        )

        inferred = (
            infer_generator(
                column_name=
                    column_name,

                sample_rows=
                    sample_rows,
            )
        )

        if inferred is not None:

            generator_map[
                column_name
            ] = inferred

            continue

        if (
            column_can_be_omitted(
                column
            )
        ):

            continue

        unsupported_required.append(
            column_name
        )

    if unsupported_required:

        raise RuntimeError(
            (
                "The date dimension contains required "
                "columns whose conventions could not "
                "be inferred safely: "
                +
                ", ".join(
                    unsupported_required
                )
                +
                ". No rows were inserted."
            )
        )

    return generator_map


# ============================================================
# BUILD MISSING DATE LIST
# ============================================================

def build_missing_dates(
    current_max_date: date,
    through_date: date,
) -> list[date]:

    if (
        through_date
        <=
        current_max_date
    ):

        return []

    dates: list[date] = []

    next_date = (
        current_max_date
        +
        timedelta(
            days=1
        )
    )

    while (
        next_date
        <=
        through_date
    ):

        dates.append(
            next_date
        )

        next_date = (
            next_date
            +
            timedelta(
                days=1
            )
        )

    return dates


# ============================================================
# BUILD INSERT ROWS
# ============================================================

def build_rows(
    missing_dates: list[date],
    generator_map: dict[
        str,
        tuple[
            str,
            CandidateFunction,
        ],
    ],
) -> list[dict]:

    rows: list[dict] = []

    for calendar_date in missing_dates:

        row: dict[str, Any] = {}

        for (
            column_name,
            (
                _generator_name,
                generator_function,
            ),
        ) in generator_map.items():

            row[
                column_name
            ] = (
                generator_function(
                    calendar_date
                )
            )

        rows.append(
            row
        )

    return rows


# ============================================================
# VERIFY CONTIGUOUS COVERAGE
# ============================================================

def verify_contiguous_coverage(
    through_date: date,
) -> dict:

    query = text(
        """
        WITH bounds AS
        (
            SELECT
                MIN(date_id)
                    AS minimum_date

            FROM
                analytics.dim_date
        ),

        expected_dates AS
        (
            SELECT
                generate_series(
                    (
                        SELECT
                            minimum_date

                        FROM
                            bounds
                    ),
                    CAST(
                        :through_date
                        AS DATE
                    ),
                    INTERVAL '1 day'
                )::DATE
                    AS expected_date
        )

        SELECT
            COUNT(*)
                AS missing_date_count

        FROM
            expected_dates expected

        LEFT JOIN
            analytics.dim_date actual

            ON
                actual.date_id =
                expected.expected_date

        WHERE
            actual.date_id
            IS NULL;
        """
    )

    with engine.connect() as connection:

        missing_count = int(
            connection
            .execute(
                query,
                {
                    "through_date":
                        through_date,
                },
            )
            .scalar_one()
        )

    return {
        "through_date":
            through_date.isoformat(),

        "missing_date_count":
            missing_count,

        "contiguous":
            (
                missing_count
                ==
                0
            ),
    }


# ============================================================
# MAIN OPERATION
# ============================================================

def ensure_date_dimension(
    through_date: date,
    apply_changes: bool,
) -> dict:

    print()
    print(
        "="
        *
        72
    )

    print(
        "DATE DIMENSION COVERAGE CHECK"
    )

    print(
        "="
        *
        72
    )

    # --------------------------------------------------------
    # DATABASE SAFETY
    # --------------------------------------------------------

    with engine.connect() as connection:

        database_name = (
            connection
            .execute(
                text(
                    """
                    SELECT
                        CURRENT_DATABASE();
                    """
                )
            )
            .scalar_one()
        )

        current_user = (
            connection
            .execute(
                text(
                    """
                    SELECT
                        CURRENT_USER;
                    """
                )
            )
            .scalar_one()
        )

    print()
    print(
        f"Database:     {database_name}"
    )

    print(
        f"User:         {current_user}"
    )

    if (
        database_name
        !=
        "ai_business_intelligence"
    ):

        raise RuntimeError(
            (
                "Wrong PostgreSQL database. "
                "Expected ai_business_intelligence."
            )
        )

    # --------------------------------------------------------
    # SCHEMA
    # --------------------------------------------------------

    table = (
        reflect_date_table()
    )

    columns = (
        inspect_columns()
    )

    print()
    print(
        "dim_date columns:"
    )

    for column in columns:

        print(
            (
                "  "
                f"{column['name']:<24} "
                f"{str(column['type']):<24} "
                f"nullable={column['nullable']}"
            )
        )

    # --------------------------------------------------------
    # CURRENT COVERAGE
    # --------------------------------------------------------

    before = (
        get_date_coverage()
    )

    current_max_date = (
        before[
            "maximum_date"
        ]
    )

    if current_max_date is None:

        raise RuntimeError(
            (
                "analytics.dim_date is empty. "
                "This script only extends an "
                "existing date dimension."
            )
        )

    if isinstance(
        current_max_date,
        datetime,
    ):

        current_max_date = (
            current_max_date.date()
        )

    print()
    print(
        "Current coverage:"
    )

    print(
        (
            "  Rows:         "
            f"{before['row_count']:,}"
        )
    )

    print(
        (
            "  Distinct:     "
            f"{before['distinct_dates']:,}"
        )
    )

    print(
        (
            "  Minimum date: "
            f"{before['minimum_date']}"
        )
    )

    print(
        (
            "  Maximum date: "
            f"{before['maximum_date']}"
        )
    )

    print(
        (
            "  Required through: "
            f"{through_date}"
        )
    )

    # --------------------------------------------------------
    # ALREADY COVERED
    # --------------------------------------------------------

    if (
        current_max_date
        >=
        through_date
    ):

        contiguous = (
            verify_contiguous_coverage(
                through_date
            )
        )

        print()
        print(
            "No extension is required."
        )

        print(
            (
                "Missing dates through target: "
                f"{contiguous['missing_date_count']}"
            )
        )

        return {
            "status":
                (
                    "ready"
                    if
                    contiguous[
                        "contiguous"
                    ]
                    else
                    "gap_detected"
                ),

            "applied":
                False,

            "before":
                before,

            "after":
                before,

            "rows_to_insert":
                0,

            "rows_inserted":
                0,

            "coverage":
                contiguous,
        }

    # --------------------------------------------------------
    # SAMPLE EXISTING CONVENTIONS
    # --------------------------------------------------------

    sample_rows = (
        load_sample_rows(
            table
        )
    )

    generator_map = (
        build_generator_map(
            table=
                table,

            sample_rows=
                sample_rows,
        )
    )

    print()
    print(
        "Inferred date-column conventions:"
    )

    for (
        column_name,
        (
            generator_name,
            _generator_function,
        ),
    ) in (
        generator_map.items()
    ):

        print(
            (
                f"  {column_name:<24} "
                f"{generator_name}"
            )
        )

    # --------------------------------------------------------
    # MISSING DATES
    # --------------------------------------------------------

    missing_dates = (
        build_missing_dates(
            current_max_date=
                current_max_date,

            through_date=
                through_date,
        )
    )

    rows = (
        build_rows(
            missing_dates=
                missing_dates,

            generator_map=
                generator_map,
        )
    )

    print()
    print(
        (
            "Dates to add: "
            f"{len(rows):,}"
        )
    )

    if rows:

        print()
        print(
            "First generated row:"
        )

        for (
            key,
            value,
        ) in (
            rows[
                0
            ]
            .items()
        ):

            print(
                f"  {key}: {value}"
            )

        print()
        print(
            "Last generated row:"
        )

        for (
            key,
            value,
        ) in (
            rows[
                -1
            ]
            .items()
        ):

            print(
                f"  {key}: {value}"
            )

    # --------------------------------------------------------
    # DRY RUN
    # --------------------------------------------------------

    if not apply_changes:

        print()
        print(
            "="
            *
            72
        )

        print(
            "DRY RUN COMPLETE"
        )

        print(
            (
                "No PostgreSQL rows were changed. "
                "Run again with --apply after "
                "reviewing the generated values."
            )
        )

        print(
            "="
            *
            72
        )

        return {
            "status":
                "dry_run",

            "applied":
                False,

            "before":
                before,

            "rows_to_insert":
                len(
                    rows
                ),

            "rows_inserted":
                0,

            "target_date":
                through_date.isoformat(),
        }

    # --------------------------------------------------------
    # INSERT
    # --------------------------------------------------------

    print()
    print(
        "Extending analytics.dim_date..."
    )

    with engine.begin() as connection:

        connection.execute(
            table.insert(),
            rows,
        )

    # --------------------------------------------------------
    # VERIFY
    # --------------------------------------------------------

    after = (
        get_date_coverage()
    )

    contiguous = (
        verify_contiguous_coverage(
            through_date
        )
    )

    inserted_count = (
        int(
            after[
                "row_count"
            ]
        )
        -
        int(
            before[
                "row_count"
            ]
        )
    )

    if (
        after[
            "maximum_date"
        ]
        <
        through_date
    ):

        raise RuntimeError(
            (
                "Date dimension extension committed, "
                "but maximum date is still earlier "
                "than the requested target."
            )
        )

    if not contiguous[
        "contiguous"
    ]:

        raise RuntimeError(
            (
                "Date dimension contains gaps after "
                "extension. Missing-date count: "
                f"{contiguous['missing_date_count']}."
            )
        )

    print()
    print(
        "="
        *
        72
    )

    print(
        "DATE DIMENSION EXTENSION SUCCESSFUL"
    )

    print(
        "="
        *
        72
    )

    print()
    print(
        (
            "Rows before:   "
            f"{before['row_count']:,}"
        )
    )

    print(
        (
            "Rows inserted: "
            f"{inserted_count:,}"
        )
    )

    print(
        (
            "Rows after:    "
            f"{after['row_count']:,}"
        )
    )

    print(
        (
            "Maximum date:  "
            f"{after['maximum_date']}"
        )
    )

    print(
        (
            "Missing dates: "
            f"{contiguous['missing_date_count']}"
        )
    )

    return {
        "status":
            "success",

        "applied":
            True,

        "before":
            before,

        "after":
            after,

        "rows_to_insert":
            len(
                rows
            ),

        "rows_inserted":
            inserted_count,

        "coverage":
            contiguous,
    }


# ============================================================
# ARGUMENT PARSER
# ============================================================

def parse_date_argument(
    value: str,
) -> date:

    try:

        return date.fromisoformat(
            value
        )

    except ValueError as error:

        raise argparse.ArgumentTypeError(
            (
                "Date must use YYYY-MM-DD format."
            )
        ) from error


def build_parser() -> argparse.ArgumentParser:

    parser = argparse.ArgumentParser(
        description=(
            "Safely extend analytics.dim_date "
            "through a requested calendar date."
        )
    )

    parser.add_argument(
        "--through",
        type=
            parse_date_argument,
        default=
            DEFAULT_THROUGH_DATE,
        help=(
            "Required date coverage, "
            "for example 2026-08-31."
        ),
    )

    parser.add_argument(
        "--apply",
        action=
            "store_true",
        help=(
            "Commit missing date rows. "
            "Without this flag the command "
            "is a dry run."
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

    try:

        result = (
            ensure_date_dimension(
                through_date=
                    args.through,

                apply_changes=
                    args.apply,
            )
        )

    except Exception as error:

        print()
        print(
            "="
            *
            72
        )

        print(
            "DATE DIMENSION CHECK FAILED"
        )

        print(
            "="
            *
            72
        )

        print()
        print(
            (
                f"{type(error).__name__}: "
                f"{str(error)}"
            )
        )

        print()
        print(
            (
                "No fact-sales refresh should be "
                "attempted until this is resolved."
            )
        )

        return 1

    if (
        result[
            "status"
        ]
        in {
            "success",
            "ready",
            "dry_run",
        }
    ):

        return 0

    return 1


if __name__ == "__main__":

    raise SystemExit(
        main()
    )