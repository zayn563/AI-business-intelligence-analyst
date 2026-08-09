import pytest

from backend.app.ingestion.reader import (
    choose_sheet_title,
    column_number_to_a1,
    extract_spreadsheet_id,
)


# ============================================================
# URL → ID
# ============================================================

def test_extract_google_spreadsheet_id_from_url():

    url = (
        "https://docs.google.com/"
        "spreadsheets/d/"
        "ABC123_xyz-987/edit"
    )

    assert (
        extract_spreadsheet_id(url)
        ==
        "ABC123_xyz-987"
    )


# ============================================================
# RAW ID
# ============================================================

def test_raw_spreadsheet_id_is_supported():

    spreadsheet_id = (
        "ABC123_xyz-987"
    )

    assert (
        extract_spreadsheet_id(
            spreadsheet_id
        )
        ==
        spreadsheet_id
    )


# ============================================================
# A1 COLUMN CONVERSION
# ============================================================

def test_column_number_to_a1():

    assert column_number_to_a1(1) == "A"

    assert column_number_to_a1(26) == "Z"

    assert column_number_to_a1(27) == "AA"

    assert column_number_to_a1(52) == "AZ"

    assert column_number_to_a1(53) == "BA"


# ============================================================
# EXACT TAB
# ============================================================

def test_choose_sheet_title_exact():

    titles = [
        "Sales",
        "Inventory",
    ]

    assert (
        choose_sheet_title(
            titles,
            "Sales",
        )
        ==
        "Sales"
    )


# ============================================================
# CASE-INSENSITIVE TAB
# ============================================================

def test_choose_sheet_title_case_insensitive():

    titles = [
        "Sales",
        "Inventory",
    ]

    assert (
        choose_sheet_title(
            titles,
            "sales",
        )
        ==
        "Sales"
    )


# ============================================================
# SINGLE TAB FALLBACK
# ============================================================

def test_choose_single_sheet_when_name_changed():

    titles = [
        "fact_sales_daily"
    ]

    assert (
        choose_sheet_title(
            titles,
            "Sales",
        )
        ==
        "fact_sales_daily"
    )


# ============================================================
# MULTIPLE TABS MUST NOT BE GUESSED
# ============================================================

def test_missing_tab_with_multiple_tabs_rejected():

    titles = [
        "fact_sales_daily",
        "Inventory",
    ]

    with pytest.raises(
        ValueError,
        match="Available tabs",
    ):

        choose_sheet_title(
            titles,
            "Sales",
        )