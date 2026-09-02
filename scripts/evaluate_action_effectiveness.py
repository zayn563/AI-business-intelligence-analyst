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
# IMPORTS
# ============================================================

from backend.app.decision.action_effectiveness import (
    evaluate_action,
    evaluate_actions,
    json_safe,
)


# ============================================================
# ARGUMENT PARSER
# ============================================================

def build_parser() -> argparse.ArgumentParser:

    parser = argparse.ArgumentParser(
        description=(
            "Evaluate KPI outcomes associated "
            "with tracked management actions."
        )
    )

    group = (
        parser
        .add_mutually_exclusive_group(
            required=True
        )
    )

    group.add_argument(
        "--action-id",
        type=int,
        help=(
            "Evaluate one tracked action."
        ),
    )

    group.add_argument(
        "--all",
        action="store_true",
        help=(
            "Evaluate eligible tracked actions."
        ),
    )

    parser.add_argument(
        "--include-open",
        action="store_true",
        help=(
            "When using --all, include OPEN "
            "and BLOCKED actions as well."
        ),
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "Calculate outcomes without persisting "
            "effectiveness records."
        ),
    )

    return parser


# ============================================================
# PRINT RESULT
# ============================================================

def print_result(
    result: dict,
) -> None:

    print(
        json.dumps(
            json_safe(
                result
            ),
            indent=2,
            default=str,
        )
    )


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

    persist = (
        not args.dry_run
    )

    # --------------------------------------------------------
    # ONE ACTION
    # --------------------------------------------------------

    if (
        args.action_id
        is not None
    ):

        result = (
            evaluate_action(
                action_id=
                    args.action_id,

                persist=
                    persist,
            )
        )

        print_result(
            result
        )

        if (
            result.get(
                "status"
            )
            ==
            "ERROR"
        ):

            return 1

        return 0

    # --------------------------------------------------------
    # ALL ACTIONS
    # --------------------------------------------------------

    statuses = (
        "COMPLETED",
        "IN_PROGRESS",
    )

    if args.include_open:

        statuses = (
            "COMPLETED",
            "IN_PROGRESS",
            "OPEN",
            "BLOCKED",
        )

    result = (
        evaluate_actions(
            statuses=
                statuses,

            persist=
                persist,
        )
    )

    print_result(
        result
    )

    if (
        result.get(
            "status"
        )
        ==
        "ERROR"
    ):

        return 1

    return 0


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    raise SystemExit(
        main()
    )