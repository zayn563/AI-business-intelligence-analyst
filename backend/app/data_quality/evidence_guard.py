from __future__ import annotations

from typing import Iterable

from .freshness_service import (
    EvidenceStatus,
    combine_evidence_statuses,
)


# ============================================================
# METRIC → DATA-DOMAIN DEPENDENCIES
# ============================================================


_METRIC_DEPENDENCIES: dict[
    str,
    tuple[str, ...],
] = {
    # --------------------------------------------------------
    # CORE SALES
    # --------------------------------------------------------

    "net_sales": (
        "sales",
    ),

    "units_sold": (
        "sales",
    ),

    "transactions": (
        "sales",
    ),

    "gross_profit": (
        "sales",
    ),

    "margin_pct": (
        "sales",
    ),

    "gross_margin": (
        "sales",
    ),

    "avg_selling_price": (
        "sales",
    ),

    "asp": (
        "sales",
    ),

    "discount_pct": (
        "sales",
    ),

    "cost_per_unit": (
        "sales",
    ),

    # --------------------------------------------------------
    # INVENTORY / AVAILABILITY
    # --------------------------------------------------------

    "stockout_rate": (
        "inventory",
    ),

    "stockout": (
        "inventory",
    ),

    "availability": (
        "inventory",
    ),

    "inventory": (
        "inventory",
    ),

    "inventory_on_hand": (
        "inventory",
    ),

    "on_hand_units": (
        "inventory",
    ),

    # --------------------------------------------------------
    # TARGETS
    # --------------------------------------------------------

    "target_attainment": (
        "sales",
        "targets",
    ),

    "sales_target_attainment": (
        "sales",
        "targets",
    ),

    "sales_target_achievement": (
        "sales",
        "targets",
    ),

    "units_target_attainment": (
        "sales",
        "targets",
    ),

    "units_target_achievement": (
        "sales",
        "targets",
    ),

    "sales_target": (
        "targets",
    ),

    "units_target": (
        "targets",
    ),

    "target_gap": (
        "sales",
        "targets",
    ),

    "sales_gap": (
        "sales",
        "targets",
    ),

    "units_gap": (
        "sales",
        "targets",
    ),

    # --------------------------------------------------------
    # PROMOTIONS
    # --------------------------------------------------------

    "promotion_effectiveness": (
        "sales",
        "promotions",
    ),

    "promotion_uplift": (
        "sales",
        "promotions",
    ),

    "promo_uplift": (
        "sales",
        "promotions",
    ),
}


# ============================================================
# NORMALIZATION
# ============================================================


def normalize_metric(
    metric: str,
) -> str:
    return (
        str(
            metric
        )
        .strip()
        .lower()
        .replace(
            " ",
            "_",
        )
        .replace(
            "-",
            "_",
        )
    )


# ============================================================
# DEPENDENCY LOOKUP
# ============================================================


def required_datasets_for_metric(
    metric: str,
) -> tuple[str, ...]:
    """
    Return analytical data domains required for a KPI.

    Unknown metrics default to the sales domain because the
    deterministic intelligence layer is primarily sales-led.
    """

    normalized = normalize_metric(
        metric
    )

    return (
        _METRIC_DEPENDENCIES
        .get(
            normalized,
            (
                "sales",
            ),
        )
    )


# ============================================================
# DATASET LOOKUP
# ============================================================


def freshness_dataset_lookup(
    freshness_report: dict,
) -> dict[
    str,
    dict,
]:
    datasets = freshness_report.get(
        "datasets",
        [],
    )

    return {
        str(
            dataset.get(
                "dataset"
            )
        ):
            dataset

        for dataset
        in datasets

        if (
            isinstance(
                dataset,
                dict,
            )
            and
            dataset.get(
                "dataset"
            )
        )
    }


# ============================================================
# ONE METRIC
# ============================================================


def evaluate_metric_evidence(
    metric: str,
    freshness_report: dict,
) -> dict:
    """
    Determine whether a metric has current analytical evidence.

    Important lifecycle guardrail:

        RESOLVED should only be considered when
        resolution_allowed is True.

    For example, a target issue must not be marked RESOLVED
    merely because current-month target records are missing.
    """

    required_datasets = (
        required_datasets_for_metric(
            metric
        )
    )

    lookup = freshness_dataset_lookup(
        freshness_report
    )

    evidence: list[dict] = []
    statuses: list[EvidenceStatus] = []

    for dataset_name in required_datasets:
        dataset = lookup.get(
            dataset_name
        )

        # ----------------------------------------------------
        # REQUIRED DATASET ABSENT
        # ----------------------------------------------------

        if dataset is None:
            status = (
                EvidenceStatus.INCOMPLETE
            )

            evidence.append(
                {
                    "dataset":
                        dataset_name,

                    "status":
                        status.value,

                    "maximum_coverage":
                        None,

                    "expected_through":
                        freshness_report.get(
                            "reference_data_through"
                        ),

                    "reason":
                        (
                            "Required analytical "
                            "dataset is absent from "
                            "the freshness report."
                        ),
                }
            )

            statuses.append(
                status
            )

            continue

        # ----------------------------------------------------
        # NORMALIZE STATUS
        # ----------------------------------------------------

        raw_status = dataset.get(
            "status",
            EvidenceStatus.INCOMPLETE.value,
        )

        try:
            status = EvidenceStatus(
                raw_status
            )

        except ValueError:
            status = (
                EvidenceStatus.INCOMPLETE
            )

        statuses.append(
            status
        )

        evidence.append(
            {
                "dataset":
                    dataset_name,

                "status":
                    status.value,

                "maximum_coverage":
                    dataset.get(
                        "maximum_coverage"
                    ),

                "expected_through":
                    dataset.get(
                        "expected_through"
                    ),

                "reason":
                    dataset.get(
                        "reason"
                    ),
            }
        )

    # --------------------------------------------------------
    # COMBINED DECISION
    # --------------------------------------------------------

    combined_status = (
        combine_evidence_statuses(
            statuses
        )
    )

    resolution_allowed = (
        combined_status
        ==
        EvidenceStatus.CURRENT
    )

    return {
        "metric":
            normalize_metric(
                metric
            ),

        "evidence_status":
            combined_status.value,

        "required_datasets":
            list(
                required_datasets
            ),

        "resolution_allowed":
            resolution_allowed,

        "evidence":
            evidence,

        "guardrail_message":
            (
                (
                    "Evidence is current. "
                    "Lifecycle resolution may "
                    "be evaluated normally."
                )
                if resolution_allowed
                else
                (
                    "Evidence is not current. "
                    "Do not infer that a "
                    "business issue is resolved "
                    "from the absence of a "
                    "current-period signal."
                )
            ),
    }


# ============================================================
# MULTIPLE METRICS
# ============================================================


def evaluate_metrics_evidence(
    metrics: Iterable[str],
    freshness_report: dict,
) -> dict:
    results = [
        evaluate_metric_evidence(
            metric,
            freshness_report,
        )
        for metric
        in metrics
    ]

    statuses = [
        EvidenceStatus(
            result[
                "evidence_status"
            ]
        )
        for result
        in results
    ]

    overall_status = (
        combine_evidence_statuses(
            statuses
        )
        if statuses
        else
        EvidenceStatus.INCOMPLETE
    )

    return {
        "evidence_status":
            overall_status.value,

        "resolution_allowed":
            (
                overall_status
                ==
                EvidenceStatus.CURRENT
            ),

        "metrics":
            results,
    }