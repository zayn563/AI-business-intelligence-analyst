from backend.app.data_quality.evidence_guard import (
    evaluate_metric_evidence,
    required_datasets_for_metric,
)

from backend.app.decision.insight_service import (
    evaluate_disappeared_insight_resolution,
)


# ============================================================
# TEST FIXTURE
# ============================================================


def freshness_report(
    *,
    sales_status: str = "CURRENT",
    inventory_status: str = "CURRENT",
    targets_status: str = "CURRENT",
    promotions_status: str = "CURRENT",
) -> dict:
    return {
        "reference_data_through":
            "2026-08-31",

        "datasets": [
            {
                "dataset":
                    "sales",

                "status":
                    sales_status,

                "maximum_coverage":
                    "2026-08-31",

                "expected_through":
                    "2026-08-31",

                "reason":
                    "Sales coverage.",
            },

            {
                "dataset":
                    "inventory",

                "status":
                    inventory_status,

                "maximum_coverage":
                    (
                        "2026-08-31"
                        if (
                            inventory_status
                            ==
                            "CURRENT"
                        )
                        else
                        "2026-07-31"
                    ),

                "expected_through":
                    "2026-08-31",

                "reason":
                    "Inventory coverage.",
            },

            {
                "dataset":
                    "targets",

                "status":
                    targets_status,

                "maximum_coverage":
                    (
                        "2026-08-01"
                        if (
                            targets_status
                            ==
                            "CURRENT"
                        )
                        else
                        "2026-07-01"
                    ),

                "expected_through":
                    "2026-08-01",

                "reason":
                    "Target coverage.",
            },

            {
                "dataset":
                    "promotions",

                "status":
                    promotions_status,

                "maximum_coverage":
                    "2026-04-30",

                "expected_through":
                    None,

                "reason":
                    "Event-based.",
            },
        ],
    }


# ============================================================
# DEPENDENCY MAPPING
# ============================================================


def test_net_sales_requires_sales_only():
    assert (
        required_datasets_for_metric(
            "net_sales"
        )
        ==
        (
            "sales",
        )
    )


def test_target_attainment_requires_sales_and_targets():
    assert (
        required_datasets_for_metric(
            "target_attainment"
        )
        ==
        (
            "sales",
            "targets",
        )
    )


def test_stockout_requires_inventory():
    assert (
        required_datasets_for_metric(
            "stockout_rate"
        )
        ==
        (
            "inventory",
        )
    )


# ============================================================
# RESOLUTION GUARD
# ============================================================


def test_current_sales_metric_can_be_evaluated_for_resolution():
    result = evaluate_metric_evidence(
        "gross_profit",
        freshness_report(),
    )

    assert (
        result[
            "evidence_status"
        ]
        ==
        "CURRENT"
    )

    assert (
        result[
            "resolution_allowed"
        ]
        is True
    )

    assert (
        result[
            "blocking_datasets"
        ]
        ==
        []
    )

    assert (
        result[
            "reference_data_through"
        ]
        ==
        "2026-08-31"
    )


def test_stale_targets_block_target_resolution():
    result = evaluate_metric_evidence(
        "target_attainment",
        freshness_report(
            targets_status="STALE"
        ),
    )

    assert (
        result[
            "evidence_status"
        ]
        ==
        "STALE"
    )

    assert (
        result[
            "resolution_allowed"
        ]
        is False
    )

    assert (
        result[
            "blocking_datasets"
        ]
        ==
        [
            "targets",
        ]
    )


def test_stale_inventory_blocks_stockout_resolution():
    result = evaluate_metric_evidence(
        "stockout_rate",
        freshness_report(
            inventory_status="STALE"
        ),
    )

    assert (
        result[
            "evidence_status"
        ]
        ==
        "STALE"
    )

    assert (
        result[
            "resolution_allowed"
        ]
        is False
    )

    assert (
        result[
            "blocking_datasets"
        ]
        ==
        [
            "inventory",
        ]
    )


def test_incomplete_required_dataset_blocks_resolution():
    result = evaluate_metric_evidence(
        "target_attainment",
        freshness_report(
            targets_status="INCOMPLETE"
        ),
    )

    assert (
        result[
            "evidence_status"
        ]
        ==
        "INCOMPLETE"
    )

    assert (
        result[
            "resolution_allowed"
        ]
        is False
    )


def test_unknown_metric_defaults_to_sales_evidence():
    result = evaluate_metric_evidence(
        "custom_sales_metric",
        freshness_report(),
    )

    assert (
        result[
            "required_datasets"
        ]
        ==
        [
            "sales",
        ]
    )

    assert (
        result[
            "resolution_allowed"
        ]
        is True
    )


# ============================================================
# DISAPPEARED INSIGHT LIFECYCLE
# ============================================================


def test_disappeared_target_issue_is_not_resolved_when_targets_stale():
    result = evaluate_disappeared_insight_resolution(
        existing={
            "primary_metric":
                "target_attainment",
        },
        freshness_report=freshness_report(
            targets_status="STALE"
        ),
    )

    assert (
        result[
            "should_resolve"
        ]
        is False
    )

    assert (
        result[
            "blocking_datasets"
        ]
        ==
        [
            "targets",
        ]
    )


def test_disappeared_stockout_issue_is_not_resolved_when_inventory_stale():
    result = evaluate_disappeared_insight_resolution(
        existing={
            "primary_metric":
                "stockout_rate",
        },
        freshness_report=freshness_report(
            inventory_status="STALE"
        ),
    )

    assert (
        result[
            "should_resolve"
        ]
        is False
    )

    assert (
        result[
            "evidence_status"
        ]
        ==
        "STALE"
    )


def test_disappeared_sales_issue_can_resolve_when_sales_current():
    result = evaluate_disappeared_insight_resolution(
        existing={
            "primary_metric":
                "gross_profit",
        },
        freshness_report=freshness_report(),
    )

    assert (
        result[
            "should_resolve"
        ]
        is True
    )

    assert (
        result[
            "evidence_status"
        ]
        ==
        "CURRENT"
    )