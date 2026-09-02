from datetime import date

from backend.app.data_quality.freshness_service import (
    EvidenceStatus,
    classify_daily_coverage,
    classify_monthly_coverage,
    combine_evidence_statuses,
    month_distance,
)


# ============================================================
# DAILY COVERAGE
# ============================================================


def test_daily_current_when_dates_match():
    result = classify_daily_coverage(
        actual_through=date(
            2026,
            8,
            31,
        ),
        expected_through=date(
            2026,
            8,
            31,
        ),
    )

    assert (
        result
        ==
        EvidenceStatus.CURRENT
    )


def test_daily_stale_when_dataset_trails_reference():
    result = classify_daily_coverage(
        actual_through=date(
            2026,
            7,
            31,
        ),
        expected_through=date(
            2026,
            8,
            31,
        ),
    )

    assert (
        result
        ==
        EvidenceStatus.STALE
    )


def test_daily_incomplete_when_coverage_missing():
    result = classify_daily_coverage(
        actual_through=None,
        expected_through=date(
            2026,
            8,
            31,
        ),
    )

    assert (
        result
        ==
        EvidenceStatus.INCOMPLETE
    )


# ============================================================
# MONTHLY COVERAGE
# ============================================================


def test_monthly_current_for_same_reference_month():
    result = classify_monthly_coverage(
        actual_through=date(
            2026,
            8,
            1,
        ),
        expected_through=date(
            2026,
            8,
            31,
        ),
    )

    assert (
        result
        ==
        EvidenceStatus.CURRENT
    )


def test_monthly_stale_when_previous_month_is_latest():
    result = classify_monthly_coverage(
        actual_through=date(
            2026,
            7,
            1,
        ),
        expected_through=date(
            2026,
            8,
            31,
        ),
    )

    assert (
        result
        ==
        EvidenceStatus.STALE
    )


def test_month_distance():
    result = month_distance(
        actual=date(
            2026,
            6,
            1,
        ),
        expected=date(
            2026,
            8,
            31,
        ),
    )

    assert (
        result
        ==
        2
    )


# ============================================================
# COMBINED STATUS
# ============================================================


def test_combined_current():
    result = combine_evidence_statuses(
        [
            EvidenceStatus.CURRENT,
            EvidenceStatus.CURRENT,
        ]
    )

    assert (
        result
        ==
        EvidenceStatus.CURRENT
    )


def test_combined_stale_blocks_current():
    result = combine_evidence_statuses(
        [
            EvidenceStatus.CURRENT,
            EvidenceStatus.STALE,
        ]
    )

    assert (
        result
        ==
        EvidenceStatus.STALE
    )


def test_combined_incomplete_has_highest_blocking_priority():
    result = combine_evidence_statuses(
        [
            EvidenceStatus.CURRENT,
            EvidenceStatus.STALE,
            EvidenceStatus.INCOMPLETE,
        ]
    )

    assert (
        result
        ==
        EvidenceStatus.INCOMPLETE
    )