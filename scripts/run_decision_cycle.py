from __future__ import annotations

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


if str(
    PROJECT_ROOT
) not in sys.path:

    sys.path.insert(
        0,
        str(
            PROJECT_ROOT
        ),
    )


# ============================================================
# IMPORT AFTER PROJECT PATH
# ============================================================

from backend.app.decision.run_service import (  # noqa: E402
    run_decision_intelligence,
)


# ============================================================
# MAIN
# ============================================================

def main() -> int:

    try:

        result = (
            run_decision_intelligence()
        )

        print(
            json.dumps(
                result,
                indent=2,
                default=str,
            )
        )

        return 0

    except Exception as error:

        print(
            json.dumps(
                {
                    "status":
                        "failed",

                    "error_type":
                        type(
                            error
                        ).__name__,

                    "error":
                        str(
                            error
                        ),
                },
                indent=2,
            )
        )

        return 1


# ============================================================
# ENTRYPOINT
# ============================================================

if __name__ == "__main__":

    raise SystemExit(
        main()
    )