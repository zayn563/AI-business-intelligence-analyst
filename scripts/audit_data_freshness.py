from __future__ import annotations

import argparse
import json
import sys

from pathlib import Path


# ============================================================
# PROJECT ROOT
# ============================================================


PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[1]
)


if (
    str(
        PROJECT_ROOT
    )
    not in
    sys.path
):
    sys.path.insert(
        0,
        str(
            PROJECT_ROOT
        ),
    )


# ============================================================
# APPLICATION
# ============================================================


from backend.app.data_quality import (
    get_data_freshness_report,
)


# ============================================================
# DEFAULT OUTPUT
# ============================================================


DEFAULT_OUTPUT = (
    PROJECT_ROOT
    /
    "data"
    /
    "validation"
    /
    "data_freshness_latest.json"
)


# ============================================================
# FORMATTING
# ============================================================


def display_value(
    value,
) -> str:
    if value is None:
        return "-"

    return str(
        value
    )


def print_separator() -> None:
    print(
        "="
        *
        110
    )


def print_table(
    report: dict,
) -> None:
    print()

    print_separator()

    print(
        (
            "AI BUSINESS INTELLIGENCE ANALYST "
            "- DATA FRESHNESS AUDIT"
        )
    )

    print_separator()

    print()

    print(
        (
            "Reference data through: "
            f"{report['reference_data_through']}"
        )
    )

    print(
        (
            "Overall evidence status: "
            f"{report['status']}"
        )
    )

    print(
        (
            "Mixed-period warning:    "
            f"{report['mixed_period_warning']}"
        )
    )

    blocking = report.get(
        "blocking_datasets",
        [],
    )

    print(
        (
            "Blocking datasets:       "
            +
            (
                ", ".join(
                    blocking
                )
                if blocking
                else
                "None"
            )
        )
    )

    print()

    headers = [
        "DATASET",
        "STATUS",
        "ROWS",
        "CADENCE",
        "COVERAGE COLUMN",
        "MAX COVERAGE",
        "EXPECTED",
        "LAG",
    ]

    widths = [
        14,
        12,
        12,
        10,
        22,
        14,
        14,
        12,
    ]

    header_line = " ".join(
        str(
            header
        ).ljust(
            width
        )
        for (
            header,
            width,
        )
        in zip(
            headers,
            widths,
            strict=True,
        )
    )

    print(
        header_line
    )

    print(
        "-"
        *
        len(
            header_line
        )
    )

    for dataset in report[
        "datasets"
    ]:
        if (
            dataset.get(
                "lag_days"
            )
            is not None
        ):
            lag = (
                f"{dataset['lag_days']}d"
            )

        elif (
            dataset.get(
                "lag_months"
            )
            is not None
        ):
            lag = (
                f"{dataset['lag_months']}mo"
            )

        else:
            lag = "-"

        values = [
            dataset[
                "dataset"
            ],

            dataset[
                "status"
            ],

            f"{dataset['row_count']:,}",

            dataset[
                "cadence"
            ],

            display_value(
                dataset.get(
                    "coverage_column"
                )
            ),

            display_value(
                dataset.get(
                    "maximum_coverage"
                )
            ),

            display_value(
                dataset.get(
                    "expected_through"
                )
            ),

            lag,
        ]

        print(
            " ".join(
                str(
                    value
                )[
                    :width
                ]
                .ljust(
                    width
                )
                for (
                    value,
                    width,
                )
                in zip(
                    values,
                    widths,
                    strict=True,
                )
            )
        )

    print()

    print(
        "DATASET DETAILS"
    )

    print(
        "-"
        *
        110
    )

    for dataset in report[
        "datasets"
    ]:
        print()

        print(
            (
                f"[{dataset['dataset'].upper()}] "
                f"{dataset['status']}"
            )
        )

        print(
            (
                "  Table:               "
                f"{dataset['relation']}"
            )
        )

        print(
            (
                "  Required this cycle: "
                f"{dataset['required_for_current_cycle']}"
            )
        )

        print(
            (
                "  Coverage field:      "
                f"{display_value(dataset.get('coverage_column'))}"
            )
        )

        print(
            (
                "  Date fields found:   "
                +
                (
                    ", ".join(
                        dataset.get(
                            "available_date_columns",
                            [],
                        )
                    )
                    or
                    "None"
                )
            )
        )

        print(
            (
                "  Min coverage:        "
                f"{display_value(dataset.get('minimum_coverage'))}"
            )
        )

        print(
            (
                "  Max coverage:        "
                f"{display_value(dataset.get('maximum_coverage'))}"
            )
        )

        print(
            (
                "  Expected through:    "
                f"{display_value(dataset.get('expected_through'))}"
            )
        )

        print(
            (
                "  Reason:              "
                f"{dataset['reason']}"
            )
        )

        print(
            "  Columns:"
        )

        for column in dataset.get(
            "columns",
            [],
        ):
            print(
                (
                    "    "
                    f"{column['ordinal_position']:>2}. "
                    f"{column['column_name']:<28} "
                    f"{column['data_type']}"
                )
            )

    print()

    print_separator()

    print(
        report[
            "message"
        ]
    )

    print_separator()


# ============================================================
# WRITE AUDIT FILE
# ============================================================


def write_report(
    report: dict,
    output_path: Path,
) -> None:
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path.write_text(
        json.dumps(
            report,
            indent=2,
            default=str,
        ),
        encoding="utf-8",
    )


# ============================================================
# CLI
# ============================================================


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Audit analytical dataset freshness "
            "against the latest sales period."
        )
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help=(
            "Print JSON instead of the "
            "human-readable table."
        ),
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=(
            "Path used to persist the "
            "freshness audit JSON."
        ),
    )

    parser.add_argument(
        "--require-current",
        action="store_true",
        help=(
            "Return exit code 2 when any "
            "required dataset is not CURRENT. "
            "Useful later for CI/deployment gates."
        ),
    )

    return parser


# ============================================================
# MAIN
# ============================================================


def main() -> int:
    parser = build_parser()

    args = parser.parse_args()

    try:
        report = (
            get_data_freshness_report()
        )

    except Exception as error:
        print(
            (
                "DATA FRESHNESS AUDIT FAILED: "
                f"{type(error).__name__}: "
                f"{error}"
            ),
            file=sys.stderr,
        )

        return 1

    write_report(
        report,
        args.output,
    )

    if args.json:
        print(
            json.dumps(
                report,
                indent=2,
                default=str,
            )
        )

    else:
        print_table(
            report
        )

        print()

        print(
            "Audit JSON saved to:"
        )

        print(
            f"  {args.output}"
        )

    if (
        args.require_current
        and
        report[
            "status"
        ]
        !=
        "CURRENT"
    ):
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )