from __future__ import annotations

import re

from dataclasses import (
    asdict,
    dataclass,
)

from datetime import (
    date,
    datetime,
    timezone,
)

from enum import StrEnum

from typing import (
    Any,
    Iterable,
)

from sqlalchemy import text
from sqlalchemy.engine import Connection

from ..database import engine


# ============================================================
# EVIDENCE STATUS
# ============================================================


class EvidenceStatus(StrEnum):
    """
    Analytical evidence availability.

    CURRENT
        The dataset covers the analytical reference period.

    STALE
        The dataset exists and contains usable data, but does
        not reach the analytical reference period.

    INCOMPLETE
        The dataset/table/coverage field is unavailable or
        does not contain enough information to establish
        usable coverage.
    """

    CURRENT = "CURRENT"
    STALE = "STALE"
    INCOMPLETE = "INCOMPLETE"


# ============================================================
# DATASET SPECIFICATION
# ============================================================


@dataclass(frozen=True)
class DatasetSpec:
    name: str
    table_schema: str
    table_name: str
    cadence: str
    required_for_current_cycle: bool
    preferred_coverage_columns: tuple[str, ...]
    coverage_expectation: str


# ============================================================
# DATASET REGISTRY
# ============================================================


DATASET_SPECS: tuple[DatasetSpec, ...] = (
    DatasetSpec(
        name="sales",
        table_schema="analytics",
        table_name="fact_sales_daily",
        cadence="daily",
        required_for_current_cycle=True,
        preferred_coverage_columns=(
            "date_id",
            "sales_date",
            "date",
        ),
        coverage_expectation=(
            "daily_through_sales_reference"
        ),
    ),

    DatasetSpec(
        name="inventory",
        table_schema="analytics",
        table_name="fact_inventory_daily",
        cadence="daily",
        required_for_current_cycle=True,
        preferred_coverage_columns=(
            "date_id",
            "inventory_date",
            "date",
        ),
        coverage_expectation=(
            "daily_through_sales_reference"
        ),
    ),

    DatasetSpec(
        name="targets",
        table_schema="analytics",
        table_name="fact_targets_monthly",
        cadence="monthly",
        required_for_current_cycle=True,
        preferred_coverage_columns=(
            "month_start",
            "target_month",
            "month_date",
            "period_start",
            "date_id",
            "target_date",
        ),
        coverage_expectation=(
            "monthly_through_sales_reference_month"
        ),
    ),

    DatasetSpec(
        name="promotions",
        table_schema="analytics",
        table_name="fact_promotions",
        cadence="event",
        required_for_current_cycle=False,
        preferred_coverage_columns=(
            "end_date",
            "promotion_end",
            "promo_end",
            "start_date",
            "promotion_start",
            "promo_start",
            "date_id",
        ),
        coverage_expectation=(
            "event_based_no_monthly_requirement"
        ),
    ),
)


# ============================================================
# IDENTIFIER SAFETY
# ============================================================


_IDENTIFIER_PATTERN = re.compile(
    r"^[A-Za-z_][A-Za-z0-9_]*$"
)


def safe_identifier(
    value: str,
) -> str:
    """
    Validate a SQL identifier before using it in a SQL string.

    Table and column names used by this service either come
    from our hard-coded registry or PostgreSQL metadata.
    """

    if not _IDENTIFIER_PATTERN.fullmatch(
        value
    ):
        raise ValueError(
            (
                "Unsafe SQL identifier: "
                f"{value!r}"
            )
        )

    return value


def qualified_table(
    spec: DatasetSpec,
) -> str:
    schema = safe_identifier(
        spec.table_schema
    )

    table = safe_identifier(
        spec.table_name
    )

    return (
        f"{schema}.{table}"
    )


# ============================================================
# DATE HELPERS
# ============================================================


def normalize_date(
    value: Any,
) -> date | None:
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
        str,
    ):
        cleaned = value.strip()

        if not cleaned:
            return None

        try:
            return date.fromisoformat(
                cleaned[:10]
            )

        except ValueError:
            return None

    return None


def month_start(
    value: date,
) -> date:
    return value.replace(
        day=1
    )


def month_distance(
    actual: date,
    expected: date,
) -> int:
    """
    Number of calendar months by which actual trails expected.

    Positive:
        actual is behind expected.

    Zero:
        same month.

    Negative:
        actual is ahead of expected.
    """

    return (
        (
            expected.year
            -
            actual.year
        )
        *
        12
        +
        (
            expected.month
            -
            actual.month
        )
    )


# ============================================================
# PURE FRESHNESS CLASSIFIERS
# ============================================================


def classify_daily_coverage(
    actual_through: date | None,
    expected_through: date,
) -> EvidenceStatus:
    if actual_through is None:
        return EvidenceStatus.INCOMPLETE

    if (
        actual_through
        >=
        expected_through
    ):
        return EvidenceStatus.CURRENT

    return EvidenceStatus.STALE


def classify_monthly_coverage(
    actual_through: date | None,
    expected_through: date,
) -> EvidenceStatus:
    if actual_through is None:
        return EvidenceStatus.INCOMPLETE

    actual_month = month_start(
        actual_through
    )

    expected_month = month_start(
        expected_through
    )

    if (
        actual_month
        >=
        expected_month
    ):
        return EvidenceStatus.CURRENT

    return EvidenceStatus.STALE


def combine_evidence_statuses(
    statuses: Iterable[
        EvidenceStatus | str
    ],
) -> EvidenceStatus:
    """
    Combine required-domain statuses.

    INCOMPLETE has the highest blocking severity because
    usable evidence cannot be established.

    STALE is next.

    CURRENT is returned only when every required status
    is CURRENT.
    """

    normalized = [
        (
            status
            if isinstance(
                status,
                EvidenceStatus,
            )
            else
            EvidenceStatus(
                status
            )
        )
        for status
        in statuses
    ]

    if not normalized:
        return EvidenceStatus.INCOMPLETE

    if (
        EvidenceStatus.INCOMPLETE
        in normalized
    ):
        return EvidenceStatus.INCOMPLETE

    if (
        EvidenceStatus.STALE
        in normalized
    ):
        return EvidenceStatus.STALE

    return EvidenceStatus.CURRENT


# ============================================================
# POSTGRESQL METADATA
# ============================================================


def relation_exists(
    connection: Connection,
    spec: DatasetSpec,
) -> bool:
    relation = qualified_table(
        spec
    )

    result = (
        connection
        .execute(
            text(
                """
                SELECT
                    TO_REGCLASS(
                        :relation
                    );
                """
            ),
            {
                "relation":
                    relation,
            },
        )
        .scalar_one_or_none()
    )

    return (
        result
        is not None
    )


def get_table_columns(
    connection: Connection,
    spec: DatasetSpec,
) -> list[dict]:
    rows = (
        connection
        .execute(
            text(
                """
                SELECT
                    column_name,
                    data_type,
                    udt_name,
                    is_nullable,
                    ordinal_position

                FROM
                    information_schema.columns

                WHERE
                    table_schema =
                        :table_schema

                    AND

                    table_name =
                        :table_name

                ORDER BY
                    ordinal_position;
                """
            ),
            {
                "table_schema":
                    spec.table_schema,

                "table_name":
                    spec.table_name,
            },
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
# COVERAGE COLUMN DISCOVERY
# ============================================================


_DATE_DATA_TYPES = {
    "date",
    "timestamp without time zone",
    "timestamp with time zone",
}


_DATE_UDT_NAMES = {
    "date",
    "timestamp",
    "timestamptz",
}


def is_date_column(
    column: dict,
) -> bool:
    data_type = (
        str(
            column.get(
                "data_type",
                "",
            )
        )
        .lower()
    )

    udt_name = (
        str(
            column.get(
                "udt_name",
                "",
            )
        )
        .lower()
    )

    return (
        data_type
        in
        _DATE_DATA_TYPES

        or

        udt_name
        in
        _DATE_UDT_NAMES
    )


def discover_date_columns(
    columns: list[dict],
) -> list[str]:
    return [
        str(
            column[
                "column_name"
            ]
        )
        for column
        in columns
        if is_date_column(
            column
        )
    ]


def date_column_score(
    column_name: str,
    spec: DatasetSpec,
) -> int:
    name = (
        column_name
        .strip()
        .lower()
    )

    score = 0

    if (
        name
        in
        spec.preferred_coverage_columns
    ):
        preferred_index = (
            spec
            .preferred_coverage_columns
            .index(
                name
            )
        )

        score += (
            1000
            -
            preferred_index
            *
            25
        )

    if (
        "end"
        in name
    ):
        score += (
            120
            if (
                spec.cadence
                ==
                "event"
            )
            else
            5
        )

    if (
        "start"
        in name
    ):
        score += (
            80
            if (
                spec.cadence
                ==
                "monthly"
            )
            else
            20
        )

    if (
        "month"
        in name
    ):
        score += (
            100
            if (
                spec.cadence
                ==
                "monthly"
            )
            else
            10
        )

    if (
        "date"
        in name
    ):
        score += 50

    if (
        name
        ==
        "date_id"
    ):
        score += 150

    return score


def select_coverage_column(
    columns: list[dict],
    spec: DatasetSpec,
) -> str | None:
    date_columns = discover_date_columns(
        columns
    )

    if not date_columns:
        return None

    ranked = sorted(
        date_columns,
        key=lambda name: (
            date_column_score(
                name,
                spec,
            ),
            name,
        ),
        reverse=True,
    )

    return ranked[0]


# ============================================================
# DATASET SUMMARY QUERIES
# ============================================================


def get_row_count(
    connection: Connection,
    spec: DatasetSpec,
) -> int:
    relation = qualified_table(
        spec
    )

    value = (
        connection
        .execute(
            text(
                (
                    "SELECT "
                    "COUNT(*) "
                    f"FROM {relation};"
                )
            )
        )
        .scalar_one()
    )

    return int(
        value
        or
        0
    )


def get_coverage_bounds(
    connection: Connection,
    spec: DatasetSpec,
    coverage_column: str,
) -> tuple[
    date | None,
    date | None,
]:
    relation = qualified_table(
        spec
    )

    column = safe_identifier(
        coverage_column
    )

    row = (
        connection
        .execute(
            text(
                f"""
                SELECT
                    MIN({column})
                        AS minimum_value,

                    MAX({column})
                        AS maximum_value

                FROM
                    {relation};
                """
            )
        )
        .mappings()
        .one()
    )

    return (
        normalize_date(
            row[
                "minimum_value"
            ]
        ),

        normalize_date(
            row[
                "maximum_value"
            ]
        ),
    )


# ============================================================
# REFERENCE PERIOD
# ============================================================


def get_sales_reference_date(
    connection: Connection,
) -> date:
    value = (
        connection
        .execute(
            text(
                """
                SELECT
                    MAX(date_id)

                FROM
                    analytics.fact_sales_daily;
                """
            )
        )
        .scalar_one_or_none()
    )

    normalized = normalize_date(
        value
    )

    if normalized is None:
        raise RuntimeError(
            (
                "Unable to establish the "
                "analytical reference date "
                "from analytics.fact_sales_daily."
            )
        )

    return normalized


# ============================================================
# DATASET STATUS
# ============================================================


def classify_dataset(
    spec: DatasetSpec,
    actual_through: date | None,
    reference_date: date,
    row_count: int,
    coverage_column: str | None,
) -> tuple[
    EvidenceStatus,
    str,
    int | None,
    int | None,
]:
    # --------------------------------------------------------
    # EVENT DATA
    # --------------------------------------------------------

    if (
        spec.cadence
        ==
        "event"
    ):
        if (
            row_count
            <=
            0
        ):
            return (
                EvidenceStatus.INCOMPLETE,
                (
                    "Event-based dataset exists "
                    "but contains no records."
                ),
                None,
                None,
            )

        return (
            EvidenceStatus.CURRENT,
            (
                "Event-based dataset. "
                "It is not required to contain "
                "a record every analytical month."
            ),
            None,
            None,
        )

    # --------------------------------------------------------
    # EMPTY OR UNUSABLE DATASET
    # --------------------------------------------------------

    if (
        row_count
        <=
        0
    ):
        return (
            EvidenceStatus.INCOMPLETE,
            (
                "Dataset exists but contains "
                "no records."
            ),
            None,
            None,
        )

    if (
        coverage_column
        is None
    ):
        return (
            EvidenceStatus.INCOMPLETE,
            (
                "No usable date/period column "
                "could be discovered."
            ),
            None,
            None,
        )

    if (
        actual_through
        is None
    ):
        return (
            EvidenceStatus.INCOMPLETE,
            (
                "The selected coverage column "
                "does not contain a usable "
                "maximum date."
            ),
            None,
            None,
        )

    # --------------------------------------------------------
    # DAILY DATASET
    # --------------------------------------------------------

    if (
        spec.cadence
        ==
        "daily"
    ):
        status = classify_daily_coverage(
            actual_through,
            reference_date,
        )

        lag_days = max(
            (
                reference_date
                -
                actual_through
            ).days,
            0,
        )

        reason = (
            (
                "Daily coverage reaches the "
                "sales analytical reference date."
            )
            if (
                status
                ==
                EvidenceStatus.CURRENT
            )
            else
            (
                "Daily coverage trails the "
                "sales analytical reference date."
            )
        )

        return (
            status,
            reason,
            lag_days,
            None,
        )

    # --------------------------------------------------------
    # MONTHLY DATASET
    # --------------------------------------------------------

    if (
        spec.cadence
        ==
        "monthly"
    ):
        status = classify_monthly_coverage(
            actual_through,
            reference_date,
        )

        lag_months = max(
            month_distance(
                actual_through,
                reference_date,
            ),
            0,
        )

        reason = (
            (
                "Monthly coverage includes "
                "the analytical reference month."
            )
            if (
                status
                ==
                EvidenceStatus.CURRENT
            )
            else
            (
                "Monthly coverage does not "
                "include the analytical "
                "reference month."
            )
        )

        return (
            status,
            reason,
            None,
            lag_months,
        )

    return (
        EvidenceStatus.INCOMPLETE,
        (
            "Unsupported dataset cadence: "
            f"{spec.cadence}."
        ),
        None,
        None,
    )


# ============================================================
# ONE DATASET REPORT
# ============================================================


def build_dataset_report(
    connection: Connection,
    spec: DatasetSpec,
    reference_date: date,
) -> dict:
    relation = qualified_table(
        spec
    )

    if not relation_exists(
        connection,
        spec,
    ):
        return {
            "dataset":
                spec.name,

            "relation":
                relation,

            "cadence":
                spec.cadence,

            "required_for_current_cycle":
                spec.required_for_current_cycle,

            "coverage_expectation":
                spec.coverage_expectation,

            "status":
                EvidenceStatus.INCOMPLETE.value,

            "reason":
                (
                    "PostgreSQL relation "
                    "does not exist."
                ),

            "row_count":
                0,

            "coverage_column":
                None,

            "available_date_columns":
                [],

            "minimum_coverage":
                None,

            "maximum_coverage":
                None,

            "expected_through":
                reference_date.isoformat(),

            "lag_days":
                None,

            "lag_months":
                None,

            "columns":
                [],
        }

    columns = get_table_columns(
        connection,
        spec,
    )

    date_columns = discover_date_columns(
        columns
    )

    coverage_column = select_coverage_column(
        columns,
        spec,
    )

    row_count = get_row_count(
        connection,
        spec,
    )

    minimum_coverage: date | None = None
    maximum_coverage: date | None = None

    if (
        coverage_column
        is not None
    ):
        (
            minimum_coverage,
            maximum_coverage,
        ) = get_coverage_bounds(
            connection,
            spec,
            coverage_column,
        )

    (
        status,
        reason,
        lag_days,
        lag_months,
    ) = classify_dataset(
        spec=spec,
        actual_through=maximum_coverage,
        reference_date=reference_date,
        row_count=row_count,
        coverage_column=coverage_column,
    )

    if (
        spec.cadence
        ==
        "event"
    ):
        expected_through = None

    elif (
        spec.cadence
        ==
        "monthly"
    ):
        expected_through = month_start(
            reference_date
        )

    else:
        expected_through = reference_date

    return {
        "dataset":
            spec.name,

        "relation":
            relation,

        "cadence":
            spec.cadence,

        "required_for_current_cycle":
            spec.required_for_current_cycle,

        "coverage_expectation":
            spec.coverage_expectation,

        "status":
            status.value,

        "reason":
            reason,

        "row_count":
            row_count,

        "coverage_column":
            coverage_column,

        "available_date_columns":
            date_columns,

        "minimum_coverage":
            (
                minimum_coverage.isoformat()
                if (
                    minimum_coverage
                    is not None
                )
                else
                None
            ),

        "maximum_coverage":
            (
                maximum_coverage.isoformat()
                if (
                    maximum_coverage
                    is not None
                )
                else
                None
            ),

        "expected_through":
            (
                expected_through.isoformat()
                if (
                    expected_through
                    is not None
                )
                else
                None
            ),

        "lag_days":
            lag_days,

        "lag_months":
            lag_months,

        "columns": [
            {
                "column_name":
                    column[
                        "column_name"
                    ],

                "data_type":
                    column[
                        "data_type"
                    ],

                "is_nullable":
                    column[
                        "is_nullable"
                    ],

                "ordinal_position":
                    column[
                        "ordinal_position"
                    ],
            }
            for column
            in columns
        ],
    }


# ============================================================
# COMPLETE FRESHNESS REPORT
# ============================================================


def get_data_freshness_report() -> dict:
    with engine.connect() as connection:
        reference_date = (
            get_sales_reference_date(
                connection
            )
        )

        datasets = [
            build_dataset_report(
                connection=connection,
                spec=spec,
                reference_date=reference_date,
            )
            for spec
            in DATASET_SPECS
        ]

    required = [
        dataset
        for dataset
        in datasets
        if dataset[
            "required_for_current_cycle"
        ]
    ]

    required_statuses = [
        EvidenceStatus(
            dataset[
                "status"
            ]
        )
        for dataset
        in required
    ]

    overall_status = (
        combine_evidence_statuses(
            required_statuses
        )
    )

    blocking_datasets = [
        dataset[
            "dataset"
        ]
        for dataset
        in required
        if (
            dataset[
                "status"
            ]
            !=
            EvidenceStatus.CURRENT.value
        )
    ]

    dataset_lookup = {
        dataset[
            "dataset"
        ]:
            dataset

        for dataset
        in datasets
    }

    sales_status = (
        dataset_lookup
        .get(
            "sales",
            {},
        )
        .get(
            "status"
        )
    )

    mixed_period_warning = (
        sales_status
        ==
        EvidenceStatus.CURRENT.value

        and

        any(
            dataset[
                "status"
            ]
            !=
            EvidenceStatus.CURRENT.value

            for dataset
            in required

            if (
                dataset[
                    "dataset"
                ]
                !=
                "sales"
            )
        )
    )

    return {
        "status":
            overall_status.value,

        "generated_at":
            (
                datetime
                .now(
                    timezone.utc
                )
                .isoformat()
            ),

        "reference_dataset":
            "sales",

        "reference_data_through":
            reference_date.isoformat(),

        "required_datasets": [
            dataset[
                "dataset"
            ]
            for dataset
            in required
        ],

        "blocking_datasets":
            blocking_datasets,

        "mixed_period_warning":
            mixed_period_warning,

        "message":
            (
                (
                    "All required analytical "
                    "datasets cover the current "
                    "sales reference period."
                )
                if (
                    overall_status
                    ==
                    EvidenceStatus.CURRENT
                )
                else
                (
                    "The warehouse contains "
                    "mixed-period analytical "
                    "evidence. Do not infer "
                    "business resolution from "
                    "missing current-period "
                    "evidence."
                )
            ),

        "datasets":
            datasets,

        "dataset_specs": [
            asdict(
                spec
            )
            for spec
            in DATASET_SPECS
        ],
    }