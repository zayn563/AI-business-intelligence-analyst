from pathlib import Path
import argparse
import sys

import pandas as pd


# ============================================================
# PROJECT ROOT
# ============================================================

ROOT = (
    Path(__file__)
    .resolve()
    .parents[1]
)


if str(ROOT) not in sys.path:

    sys.path.insert(
        0,
        str(ROOT),
    )


# ============================================================
# PROJECT IMPORTS
# ============================================================

from backend.app.ingestion.reader import (
    list_google_sheet_titles,
    read_source_dataframe,
)

from backend.app.ingestion.transformer import (
    apply_refresh_mapping_overrides,
    required_mapping_gaps,
)

from backend.app.semantic.mapper import (
    map_profile_to_canonical,
)

from backend.app.semantic.profiler import (
    profile_dataset,
)


# ============================================================
# MAIN
# ============================================================

def main():

    parser = argparse.ArgumentParser(
        description=(
            "Inspect and test a Google Sheets "
            "business-data source."
        )
    )

    parser.add_argument(
        "--sheet-url",
        required=True,
    )

    parser.add_argument(
        "--sheet-name",
        default=None,
    )

    parser.add_argument(
        "--rows",
        type=int,
        default=5,
    )

    parser.add_argument(
        "--list-tabs",
        action="store_true",
    )

    args = parser.parse_args()


    # ========================================================
    # TAB DISCOVERY
    # ========================================================

    print(
        "\n============================================"
    )

    print(
        "GOOGLE SPREADSHEET INSPECTION"
    )

    print(
        "============================================"
    )

    titles = (
        list_google_sheet_titles(
            args.sheet_url
        )
    )

    print(
        "\nAVAILABLE TABS"
    )

    for index, title in enumerate(
        titles,
        start=1,
    ):

        print(
            f"{index}. {title}"
        )

    if args.list_tabs:
        return


    # ========================================================
    # SELECT TAB
    # ========================================================

    if args.sheet_name:

        selected_sheet = (
            args.sheet_name
        )

    elif len(titles) == 1:

        selected_sheet = (
            titles[0]
        )

    else:

        raise ValueError(
            "Multiple tabs exist. "
            "Use --sheet-name followed "
            "by the required tab title."
        )


    source = {
        "source_type":
            "google_sheets",

        "source_location":
            args.sheet_url,

        "sheet_name":
            selected_sheet,
    }


    # ========================================================
    # READ
    # ========================================================

    print(
        "\n============================================"
    )

    print(
        "GOOGLE SHEETS CONNECTION TEST"
    )

    print(
        "============================================"
    )

    print(
        f"\nRequested tab: "
        f"{selected_sheet}"
    )

    print(
        f"Requested rows: "
        f"{args.rows}"
    )

    print(
        "\nReading Google Sheet..."
    )

    dataframe = (
        read_source_dataframe(
            source,
            max_rows=args.rows,
        )
    )


    print(
        "\nCONNECTION SUCCESSFUL"
    )

    print(
        f"\nRows read: "
        f"{len(dataframe)}"
    )

    print(
        f"Columns found: "
        f"{len(dataframe.columns)}"
    )

    print(
        "\nHEADERS"
    )

    print(
        dataframe.columns.tolist()
    )

    print(
        "\nDATA SAMPLE"
    )

    if dataframe.empty:

        print(
            "No rows found."
        )

    else:

        print(
            dataframe
            .head(args.rows)
            .to_string(
                index=False
            )
        )


    # ========================================================
    # SEMANTIC PROFILE
    # ========================================================

    profile = (
        profile_dataset(
            columns=list(
                dataframe.columns
            ),
            sample_rows=(
                dataframe
                .head(args.rows)
                .to_dict(
                    "records"
                )
            ),
        )
    )


    mapping = (
        map_profile_to_canonical(
            profile
        )
    )

    mapping = (
        apply_refresh_mapping_overrides(
            mapping
        )
    )

    mappings = (
        mapping[
            "mappings"
        ]
    )


    # ========================================================
    # DISPLAY MAPPING
    # ========================================================

    print(
        "\n============================================"
    )

    print(
        "SEMANTIC COLUMN MAPPING"
    )

    print(
        "============================================"
    )


    mapping_table = pd.DataFrame(
        mappings
    )

    if mapping_table.empty:

        print(
            "No mappings found."
        )

    else:

        print(
            mapping_table[
                [
                    "source_column",
                    "canonical_field",
                    "confidence",
                    "method",
                    "status",
                ]
            ]
            .to_string(
                index=False
            )
        )


    # ========================================================
    # WAREHOUSE COMPATIBILITY
    # ========================================================

    gaps = (
        required_mapping_gaps(
            mappings
        )
    )


    print(
        "\n============================================"
    )

    print(
        "WAREHOUSE COMPATIBILITY"
    )

    print(
        "============================================"
    )


    if gaps:

        print(
            "\nMissing required mappings:"
        )

        for gap in gaps:

            print(
                f"- {gap}"
            )

    else:

        print(
            "\nAll required sales fields "
            "were mapped successfully."
        )


if __name__ == "__main__":

    main()