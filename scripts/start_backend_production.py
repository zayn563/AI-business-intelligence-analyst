from __future__ import annotations

import json
import os
import sys

from pathlib import Path

import uvicorn


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
# DEFAULTS
# ============================================================


DEFAULT_HOST = (
    "0.0.0.0"
)


DEFAULT_PORT = (
    8000
)


DEFAULT_GOOGLE_CREDENTIAL_PATH = (
    PROJECT_ROOT
    /
    "secrets"
    /
    "google-service-account.json"
)


# ============================================================
# HELPERS
# ============================================================


def environment_text(
    name: str,
) -> str | None:
    value = os.getenv(
        name
    )

    if value is None:
        return None

    cleaned = value.strip()

    if not cleaned:
        return None

    return cleaned


def runtime_port() -> int:
    raw_port = (
        environment_text(
            "PORT"
        )
    )

    if raw_port is None:
        return (
            DEFAULT_PORT
        )

    try:
        port = int(
            raw_port
        )

    except ValueError as error:
        raise RuntimeError(
            (
                "PORT must be an integer. "
                f"Received: {raw_port!r}"
            )
        ) from error

    if not (
        1
        <=
        port
        <=
        65535
    ):
        raise RuntimeError(
            (
                "PORT must be between "
                "1 and 65535."
            )
        )

    return port


# ============================================================
# GOOGLE SERVICE ACCOUNT MATERIALIZATION
# ============================================================


def google_credential_path() -> Path:
    configured_path = (
        environment_text(
            "GOOGLE_APPLICATION_CREDENTIALS"
        )
    )

    if configured_path:
        return Path(
            configured_path
        )

    return (
        DEFAULT_GOOGLE_CREDENTIAL_PATH
    )


def materialize_google_credentials() -> Path | None:
    """
    Production deployments must never commit the Google
    service-account JSON to GitHub or bake it into Docker.

    Railway stores the JSON in:

        GOOGLE_SERVICE_ACCOUNT_JSON

    At container startup we validate the JSON and write it to:

        /app/secrets/google-service-account.json

    which preserves compatibility with the existing Google
    Sheets ingestion implementation.
    """

    raw_credentials = (
        environment_text(
            "GOOGLE_SERVICE_ACCOUNT_JSON"
        )
    )

    credential_path = (
        google_credential_path()
    )

    # --------------------------------------------------------
    # SECRET SUPPLIED THROUGH CLOUD ENVIRONMENT
    # --------------------------------------------------------

    if raw_credentials:
        try:
            parsed = json.loads(
                raw_credentials
            )

        except json.JSONDecodeError as error:
            raise RuntimeError(
                (
                    "GOOGLE_SERVICE_ACCOUNT_JSON "
                    "is not valid JSON."
                )
            ) from error

        if not isinstance(
            parsed,
            dict,
        ):
            raise RuntimeError(
                (
                    "GOOGLE_SERVICE_ACCOUNT_JSON "
                    "must contain a JSON object."
                )
            )

        required_fields = {
            "type",
            "project_id",
            "private_key",
            "client_email",
        }

        missing_fields = sorted(
            required_fields
            -
            set(
                parsed.keys()
            )
        )

        if missing_fields:
            raise RuntimeError(
                (
                    "Google service-account JSON "
                    "is missing required fields: "
                    +
                    ", ".join(
                        missing_fields
                    )
                )
            )

        credential_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        credential_path.write_text(
            json.dumps(
                parsed,
                indent=2,
            ),
            encoding="utf-8",
        )

        try:
            credential_path.chmod(
                0o600
            )

        except OSError:
            pass

        os.environ[
            "GOOGLE_APPLICATION_CREDENTIALS"
        ] = str(
            credential_path
        )

        print(
            (
                "Google service-account "
                "credentials materialized "
                "successfully."
            ),
            flush=True,
        )

        return (
            credential_path
        )

    # --------------------------------------------------------
    # EXISTING FILE
    # --------------------------------------------------------

    if credential_path.exists():
        os.environ[
            "GOOGLE_APPLICATION_CREDENTIALS"
        ] = str(
            credential_path
        )

        print(
            (
                "Using existing Google "
                "service-account credential file."
            ),
            flush=True,
        )

        return (
            credential_path
        )

    # --------------------------------------------------------
    # NO GOOGLE CREDENTIAL
    #
    # Backend can still start. Google source refresh operations
    # will be unavailable until the secret is configured.
    # --------------------------------------------------------

    print(
        (
            "WARNING: Google service-account "
            "credentials are not configured. "
            "Google Sheets refresh operations "
            "will not work."
        ),
        flush=True,
    )

    return None


# ============================================================
# PRODUCTION ENVIRONMENT SUMMARY
#
# Never print passwords, tokens, JSON credentials or complete
# database URLs.
# ============================================================


def print_runtime_summary(
    host: str,
    port: int,
) -> None:
    print(
        "="
        *
        72,
        flush=True,
    )

    print(
        (
            "AI BUSINESS INTELLIGENCE ANALYST "
            "- PRODUCTION STARTUP"
        ),
        flush=True,
    )

    print(
        "="
        *
        72,
        flush=True,
    )

    print(
        f"Host: {host}",
        flush=True,
    )

    print(
        f"Port: {port}",
        flush=True,
    )

    print(
        (
            "Database configured: "
            f"{bool(environment_text('DB_HOST'))}"
        ),
        flush=True,
    )

    print(
        (
            "Ollama configured: "
            f"{bool(environment_text('OLLAMA_HOST'))}"
        ),
        flush=True,
    )

    print(
        (
            "Google credentials configured: "
            f"{bool(environment_text('GOOGLE_SERVICE_ACCOUNT_JSON'))}"
        ),
        flush=True,
    )

    print(
        "="
        *
        72,
        flush=True,
    )


# ============================================================
# MAIN
# ============================================================


def main() -> None:
    host = (
        environment_text(
            "HOST"
        )
        or
        DEFAULT_HOST
    )

    port = (
        runtime_port()
    )

    materialize_google_credentials()

    print_runtime_summary(
        host=
            host,

        port=
            port,
    )

    uvicorn.run(
        "backend.app.main:app",

        host=
            host,

        port=
            port,

        workers=
            1,

        proxy_headers=
            True,

        forwarded_allow_ips=
            "*",

        access_log=
            True,

        log_level=
            (
                environment_text(
                    "LOG_LEVEL"
                )
                or
                "info"
            ),
    )


if __name__ == "__main__":
    main()