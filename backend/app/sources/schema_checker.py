import hashlib
import json

from ..semantic.profiler import (
    normalize_header,
)


# ============================================================
# SCHEMA FINGERPRINT
#
# We sort normalized headers so simply rearranging columns
# does not count as schema drift.
# ============================================================

def schema_fingerprint(
    columns: list[str],
) -> str:

    normalized_columns = sorted(

        normalize_header(
            column
        )

        for column
        in columns
    )


    payload = json.dumps(
        normalized_columns,
        separators=(
            ",",
            ":",
        ),
    )


    return hashlib.sha256(
        payload.encode(
            "utf-8"
        )
    ).hexdigest()


# ============================================================
# SCHEMA CHANGE CHECK
# ============================================================

def has_schema_changed(
    previous_fingerprint: str | None,
    current_fingerprint: str,
) -> bool:

    if previous_fingerprint is None:
        return True


    return (
        previous_fingerprint
        != current_fingerprint
    )