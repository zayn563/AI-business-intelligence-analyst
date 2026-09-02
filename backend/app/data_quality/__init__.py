"""
Data-quality and analytical evidence guardrails.

This package provides:

1. Dataset-level freshness auditing.
2. Cross-domain evidence status.
3. Guardrails that prevent analytical workflows from
   treating missing or stale evidence as current evidence.

Business KPI calculation remains outside this package.
"""

from .evidence_guard import (
    evaluate_metric_evidence,
    evaluate_metrics_evidence,
    required_datasets_for_metric,
)

from .freshness_service import (
    DATASET_SPECS,
    EvidenceStatus,
    classify_daily_coverage,
    classify_monthly_coverage,
    combine_evidence_statuses,
    get_data_freshness_report,
)


__all__ = [
    "DATASET_SPECS",
    "EvidenceStatus",
    "classify_daily_coverage",
    "classify_monthly_coverage",
    "combine_evidence_statuses",
    "evaluate_metric_evidence",
    "evaluate_metrics_evidence",
    "get_data_freshness_report",
    "required_datasets_for_metric",
]