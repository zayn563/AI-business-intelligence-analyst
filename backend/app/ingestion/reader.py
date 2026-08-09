from pathlib import Path

import pandas as pd


# ============================================================
# PROJECT ROOT
# ============================================================

ROOT = (
    Path(__file__)
    .resolve()
    .parents[3]
)


# ============================================================
# RESOLVE LOCAL SOURCE PATH
# ============================================================

def resolve_source_path(
    source_location: str,
) -> Path:

    path = Path(
        source_location
    )


    if not path.is_absolute():

        path = (
            ROOT
            / path
        )


    return path.resolve()


# ============================================================
# READ DATA SOURCE
# ============================================================

def read_source_dataframe(
    source: dict,
) -> pd.DataFrame:

    source_type = source[
        "source_type"
    ]


    if source_type == "csv":

        path = resolve_source_path(
            source[
                "source_location"
            ]
        )


        if not path.exists():

            raise FileNotFoundError(
                f"CSV source does not exist: "
                f"{path}"
            )


        return pd.read_csv(
            path
        )


    if source_type == "google_sheets":

        raise NotImplementedError(
            "Google Sheets reader will be "
            "implemented in the next phase."
        )


    raise ValueError(
        f"Unsupported source type: "
        f"{source_type}"
    )