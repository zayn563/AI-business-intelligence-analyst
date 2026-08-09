from pathlib import Path
import json
import re

import pandas as pd

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from ..config import settings


# ============================================================
# PROJECT ROOT
# ============================================================

ROOT = (
    Path(__file__)
    .resolve()
    .parents[3]
)


# ============================================================
# GOOGLE SHEETS SETTINGS
# ============================================================

GOOGLE_SHEETS_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly"
]

GOOGLE_READ_CHUNK_SIZE = 10_000


# ============================================================
# LOCAL PATH
# ============================================================

def resolve_source_path(
    source_location: str,
) -> Path:

    path = Path(
        source_location
    )

    if not path.is_absolute():
        path = ROOT / path

    return path.resolve()


# ============================================================
# GOOGLE SPREADSHEET ID
# ============================================================

def extract_spreadsheet_id(
    source_location: str,
) -> str:

    source_location = (
        source_location
        .strip()
    )

    match = re.search(
        r"/spreadsheets/d/([A-Za-z0-9_-]+)",
        source_location,
    )

    if match:
        return match.group(1)

    if not source_location:
        raise ValueError(
            "Google Sheets source location "
            "cannot be empty."
        )

    return source_location


# ============================================================
# COLUMN NUMBER → A1 LETTER
# ============================================================

def column_number_to_a1(
    column_number: int,
) -> str:

    if column_number < 1:
        raise ValueError(
            "Column number must be >= 1."
        )

    result = ""

    while column_number:

        column_number, remainder = divmod(
            column_number - 1,
            26,
        )

        result = (
            chr(65 + remainder)
            + result
        )

    return result


# ============================================================
# GOOGLE CREDENTIALS
# ============================================================

def get_google_credentials():

    credential_file = (
        settings.google_service_account_file
    )

    if not credential_file:
        raise ValueError(
            "GOOGLE_SERVICE_ACCOUNT_FILE "
            "is not configured in .env."
        )

    credential_path = Path(
        credential_file
    )

    if not credential_path.is_absolute():
        credential_path = (
            ROOT
            / credential_path
        )

    credential_path = (
        credential_path.resolve()
    )

    if not credential_path.exists():
        raise FileNotFoundError(
            "Google service-account file "
            f"not found: {credential_path}"
        )

    return (
        service_account
        .Credentials
        .from_service_account_file(
            str(credential_path),
            scopes=GOOGLE_SHEETS_SCOPES,
        )
    )


# ============================================================
# GOOGLE API CLIENT
# ============================================================

def build_google_sheets_service():

    return build(
        "sheets",
        "v4",
        credentials=get_google_credentials(),
        cache_discovery=False,
    )


# ============================================================
# FRIENDLY GOOGLE ERROR
# ============================================================

def google_error_message(
    error: HttpError,
) -> str:

    try:

        content = error.content

        if isinstance(content, bytes):
            content = content.decode(
                "utf-8"
            )

        payload = json.loads(
            content
        )

        message = (
            payload
            .get("error", {})
            .get("message")
        )

        if message:
            return message

    except Exception:
        pass

    text = str(error).strip()

    return (
        text
        or repr(error)
    )


# ============================================================
# SPREADSHEET METADATA
# ============================================================

def get_google_sheet_metadata(
    source_location: str,
) -> list[dict]:

    spreadsheet_id = (
        extract_spreadsheet_id(
            source_location
        )
    )

    service = (
        build_google_sheets_service()
    )

    try:

        response = (
            service
            .spreadsheets()
            .get(
                spreadsheetId=spreadsheet_id,
                includeGridData=False,
                fields=(
                    "sheets("
                    "properties("
                    "sheetId,"
                    "title,"
                    "index,"
                    "sheetType,"
                    "hidden"
                    ")"
                    ")"
                ),
            )
            .execute()
        )

    except HttpError as error:

        raise ValueError(
            "Unable to read Google spreadsheet metadata. "
            f"Google API message: "
            f"{google_error_message(error)}"
        ) from error

    result = []

    for sheet in response.get(
        "sheets",
        [],
    ):

        properties = sheet.get(
            "properties",
            {},
        )

        result.append(
            {
                "sheet_id":
                    properties.get(
                        "sheetId"
                    ),

                "title":
                    properties.get(
                        "title"
                    ),

                "index":
                    properties.get(
                        "index"
                    ),

                "sheet_type":
                    properties.get(
                        "sheetType"
                    ),

                "hidden":
                    properties.get(
                        "hidden",
                        False,
                    ),
            }
        )

    return result


# ============================================================
# LIST GOOGLE WORKSHEET TITLES
# ============================================================

def list_google_sheet_titles(
    source_location: str,
) -> list[str]:

    metadata = (
        get_google_sheet_metadata(
            source_location
        )
    )

    return [
        item["title"]
        for item in metadata
        if item.get("title")
    ]


# ============================================================
# RESOLVE WORKSHEET NAME
# ============================================================

def choose_sheet_title(
    available_titles: list[str],
    requested_title: str | None,
) -> str:

    titles = [
        str(title).strip()
        for title in available_titles
        if str(title).strip()
    ]

    if not titles:
        raise ValueError(
            "The spreadsheet contains "
            "no readable worksheet tabs."
        )

    # --------------------------------------------------------
    # No requested tab
    # --------------------------------------------------------

    if not requested_title:

        if len(titles) == 1:
            return titles[0]

        raise ValueError(
            "sheet_name is required because "
            "the spreadsheet contains multiple tabs: "
            f"{titles}"
        )

    requested_title = (
        requested_title.strip()
    )

    # --------------------------------------------------------
    # Exact match
    # --------------------------------------------------------

    if requested_title in titles:
        return requested_title

    # --------------------------------------------------------
    # Case-insensitive match
    # --------------------------------------------------------

    matches = [
        title
        for title in titles
        if title.casefold()
        == requested_title.casefold()
    ]

    if len(matches) == 1:
        return matches[0]

    # --------------------------------------------------------
    # Whitespace-normalized match
    # --------------------------------------------------------

    requested_normalized = (
        " ".join(
            requested_title.split()
        )
        .casefold()
    )

    matches = [
        title
        for title in titles
        if (
            " ".join(
                title.split()
            )
            .casefold()
            ==
            requested_normalized
        )
    ]

    if len(matches) == 1:
        return matches[0]

    # --------------------------------------------------------
    # If there is ONLY ONE tab, use it.
    #
    # This makes a single-tab live source robust to an
    # accidental tab rename.
    # --------------------------------------------------------

    if len(titles) == 1:

        return titles[0]

    # --------------------------------------------------------
    # Multiple tabs: never guess.
    # --------------------------------------------------------

    raise ValueError(
        f"Google worksheet/tab "
        f"'{requested_title}' was not found. "
        f"Available tabs: {titles}"
    )


# ============================================================
# A1 SHEET QUOTING
# ============================================================

def quote_sheet_name(
    sheet_name: str,
) -> str:

    escaped = (
        sheet_name.replace(
            "'",
            "''",
        )
    )

    return (
        f"'{escaped}'"
    )


# ============================================================
# NORMALIZE ROW WIDTH
# ============================================================

def normalize_google_row(
    row: list,
    width: int,
) -> list:

    result = list(row)

    if len(result) < width:

        result.extend(
            [None]
            * (
                width
                - len(result)
            )
        )

    return result[:width]


# ============================================================
# GOOGLE SHEET READER
# ============================================================

def read_google_sheet(
    source: dict,
    max_rows: int | None = None,
) -> pd.DataFrame:

    source_location = source[
        "source_location"
    ]

    spreadsheet_id = (
        extract_spreadsheet_id(
            source_location
        )
    )

    requested_sheet_name = (
        source.get(
            "sheet_name"
        )
    )

    # --------------------------------------------------------
    # Discover actual tabs first.
    # --------------------------------------------------------

    available_titles = (
        list_google_sheet_titles(
            source_location
        )
    )

    resolved_sheet_name = (
        choose_sheet_title(
            available_titles,
            requested_sheet_name,
        )
    )

    sheet_reference = (
        quote_sheet_name(
            resolved_sheet_name
        )
    )

    service = (
        build_google_sheets_service()
    )

    values_api = (
        service
        .spreadsheets()
        .values()
    )

    # ========================================================
    # HEADER
    #
    # Explicit cell range instead of 1:1.
    # ========================================================

    header_range = (
        f"{sheet_reference}!"
        f"A1:ZZZ1"
    )

    try:

        header_response = (
            values_api
            .get(
                spreadsheetId=spreadsheet_id,
                range=header_range,
                majorDimension="ROWS",
                valueRenderOption="FORMATTED_VALUE",
            )
            .execute()
        )

    except HttpError as error:

        raise ValueError(
            f"Unable to read worksheet "
            f"'{resolved_sheet_name}'. "
            f"Range: {header_range}. "
            f"Google API message: "
            f"{google_error_message(error)}"
        ) from error

    header_values = (
        header_response.get(
            "values",
            [],
        )
    )

    if not header_values:

        raise ValueError(
            f"Worksheet "
            f"'{resolved_sheet_name}' "
            "contains no header row."
        )

    headers = [
        str(value).strip()
        for value
        in header_values[0]
    ]

    if not headers:

        raise ValueError(
            f"Worksheet "
            f"'{resolved_sheet_name}' "
            "has an empty header row."
        )

    if any(
        not header
        for header in headers
    ):

        raise ValueError(
            f"Worksheet "
            f"'{resolved_sheet_name}' "
            "contains blank column headers."
        )

    final_column = (
        column_number_to_a1(
            len(headers)
        )
    )

    # ========================================================
    # SMALL TEST READ
    # ========================================================

    if max_rows is not None:

        if max_rows < 1:

            return pd.DataFrame(
                columns=headers
            )

        end_row = (
            max_rows + 1
        )

        data_range = (
            f"{sheet_reference}!"
            f"A2:"
            f"{final_column}"
            f"{end_row}"
        )

        try:

            response = (
                values_api
                .get(
                    spreadsheetId=
                        spreadsheet_id,

                    range=
                        data_range,

                    majorDimension=
                        "ROWS",

                    valueRenderOption=
                        "UNFORMATTED_VALUE",

                    dateTimeRenderOption=
                        "FORMATTED_STRING",
                )
                .execute()
            )

        except HttpError as error:

            raise ValueError(
                f"Unable to read worksheet "
                f"'{resolved_sheet_name}'. "
                f"Range: {data_range}. "
                f"Google API message: "
                f"{google_error_message(error)}"
            ) from error

        rows = response.get(
            "values",
            [],
        )

        normalized_rows = [
            normalize_google_row(
                row,
                len(headers),
            )
            for row in rows
        ]

        return pd.DataFrame(
            normalized_rows,
            columns=headers,
        )

    # ========================================================
    # FULL CHUNKED READ
    # ========================================================

    all_rows = []

    start_row = 2

    while True:

        end_row = (
            start_row
            + GOOGLE_READ_CHUNK_SIZE
            - 1
        )

        data_range = (
            f"{sheet_reference}!"
            f"A{start_row}:"
            f"{final_column}"
            f"{end_row}"
        )

        try:

            response = (
                values_api
                .get(
                    spreadsheetId=
                        spreadsheet_id,

                    range=
                        data_range,

                    majorDimension=
                        "ROWS",

                    valueRenderOption=
                        "UNFORMATTED_VALUE",

                    dateTimeRenderOption=
                        "FORMATTED_STRING",
                )
                .execute()
            )

        except HttpError as error:

            raise ValueError(
                "Google Sheets full read failed. "
                f"Worksheet: "
                f"'{resolved_sheet_name}'. "
                f"Range: {data_range}. "
                f"Google API message: "
                f"{google_error_message(error)}"
            ) from error

        rows = response.get(
            "values",
            [],
        )

        if not rows:
            break

        all_rows.extend(
            [
                normalize_google_row(
                    row,
                    len(headers),
                )
                for row in rows
            ]
        )

        if len(rows) < GOOGLE_READ_CHUNK_SIZE:
            break

        start_row = (
            end_row + 1
        )

    return pd.DataFrame(
        all_rows,
        columns=headers,
    )


# ============================================================
# UNIVERSAL SOURCE READER
# ============================================================

def read_source_dataframe(
    source: dict,
    max_rows: int | None = None,
) -> pd.DataFrame:

    source_type = source[
        "source_type"
    ]

    # --------------------------------------------------------
    # CSV
    # --------------------------------------------------------

    if source_type == "csv":

        path = resolve_source_path(
            source[
                "source_location"
            ]
        )

        if not path.exists():

            raise FileNotFoundError(
                "CSV source does not exist: "
                f"{path}"
            )

        return pd.read_csv(
            path,
            nrows=max_rows,
        )

    # --------------------------------------------------------
    # Google Sheets
    # --------------------------------------------------------

    if source_type == "google_sheets":

        return read_google_sheet(
            source=source,
            max_rows=max_rows,
        )

    # --------------------------------------------------------
    # Unsupported
    # --------------------------------------------------------

    raise ValueError(
        "Unsupported source type: "
        f"{source_type}"
    )