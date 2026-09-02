from __future__ import annotations

import argparse
import json
import sys
import traceback
from pathlib import Path


# ============================================================
# PROJECT ROOT
# ============================================================

PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[1]
)


if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(PROJECT_ROOT),
    )


# ============================================================
# IMPORT APPLICATION
# ============================================================

from fastapi.testclient import TestClient

from backend.app.main import app


# ============================================================
# DISPLAY HELPERS
# ============================================================

SEPARATOR = (
    "="
    *
    72
)


def print_section(
    title: str,
) -> None:

    print()
    print(
        SEPARATOR
    )
    print(
        title
    )
    print(
        SEPARATOR
    )


def print_json_or_text(
    raw_text: str,
) -> None:

    clean_text = (
        raw_text
        .strip()
    )

    if not clean_text:

        print(
            "<empty response>"
        )

        return

    try:

        payload = (
            json.loads(
                clean_text
            )
        )

        print(
            json.dumps(
                payload,
                indent=2,
                default=str,
            )
        )

    except json.JSONDecodeError:

        print(
            clean_text
        )


# ============================================================
# RUN DIAGNOSTIC
# ============================================================

def diagnose(
    question: str,
) -> int:

    print_section(
        "ANALYST REQUEST DIAGNOSTIC"
    )

    print(
        "Question:"
    )

    print(
        question
    )

    print_section(
        "TESTING FASTAPI DIRECTLY"
    )

    client = TestClient(
        app,
        raise_server_exceptions=True,
    )

    try:

        response = (
            client.post(
                "/analyst/ask",
                json={
                    "question":
                        question,
                },
            )
        )

    except Exception as error:

        print(
            "UNHANDLED BACKEND EXCEPTION"
        )

        print()

        print(
            "Exception type:"
        )

        print(
            type(error).__name__
        )

        print()

        print(
            "Exception message:"
        )

        print(
            str(error)
        )

        print_section(
            "FULL TRACEBACK"
        )

        traceback.print_exc()

        print_section(
            "DIAGNOSTIC RESULT"
        )

        print(
            "The request caused an "
            "unhandled exception inside "
            "the FastAPI analyst stack."
        )

        return 1

    print(
        "HTTP status:",
        response.status_code,
    )

    print_section(
        "RESPONSE BODY"
    )

    print_json_or_text(
        response.text
    )

    print_section(
        "DIAGNOSTIC RESULT"
    )

    if response.status_code >= 500:

        print(
            "FastAPI handled the request "
            "but returned a server-side error."
        )

        return 1

    if response.status_code >= 400:

        print(
            "FastAPI rejected the request "
            "at the API or validation layer."
        )

        return 1

    print(
        "FastAPI completed the request "
        "without a server-side exception."
    )

    return 0


# ============================================================
# ARGUMENTS
# ============================================================

def build_parser() -> argparse.ArgumentParser:

    parser = argparse.ArgumentParser(
        description=(
            "Run an analyst request directly "
            "against the FastAPI application "
            "and expose full backend exceptions."
        )
    )

    parser.add_argument(
        "question",
        nargs="?",
        default=(
            "how can we improve sales "
            "in regions which require attention?"
        ),
        help=(
            "Business question to test."
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

    question = (
        str(
            args.question
        )
        .strip()
    )

    if not question:

        print(
            "Question cannot be empty."
        )

        return 2

    return diagnose(
        question
    )


if __name__ == "__main__":
    raise SystemExit(
        main()
    )