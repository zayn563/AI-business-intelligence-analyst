from datetime import date
from typing import (
    Any,
    Literal,
)

from pydantic import (
    BaseModel,
    Field,
)


# ============================================================
# SUPPORTED ANALYSIS TYPES
# ============================================================

AnalysisType = Literal[
    "latest_changes",
    "diagnostic",
    "targets",
    "promotions",
    "unsupported",
]


# ============================================================
# SUPPORTED METRICS
# ============================================================

MetricName = Literal[
    "net_sales",
    "units_sold",
    "transactions",
    "gross_profit",
    "margin_pct",
    "avg_selling_price",
    "discount_pct",
    "cost_per_unit",
    "stockout_rate",
]


# ============================================================
# SUPPORTED DIMENSIONS
# ============================================================

DimensionName = Literal[
    "overall",
    "region",
    "city",
    "channel",
    "category",
    "brand",
    "product",
    "store",
    "salesperson",
]


# ============================================================
# ANALYST INTENT
# ============================================================

class AnalystIntent(BaseModel):

    analysis_type: AnalysisType

    metric: MetricName | None = None

    dimension: DimensionName | None = None

    dimension_value: str | None = None

    current_start: date | None = None
    current_end: date | None = None

    comparison_start: date | None = None
    comparison_end: date | None = None

    target_month: date | None = None

    promotion_start: date | None = None
    promotion_end: date | None = None

    confidence: float = Field(
        default=0.50,
        ge=0.0,
        le=1.0,
    )


# ============================================================
# ASK REQUEST
# ============================================================

class AnalystAskRequest(BaseModel):

    question: str = Field(
        min_length=2,
        max_length=1000,
    )


# ============================================================
# ASK RESPONSE
# ============================================================

class AnalystAskResponse(BaseModel):

    status: str

    question: str

    answer: str

    intent: AnalystIntent

    parser: str

    tool_used: str | None = None

    # True when Ollama participated in either intent parsing
    # or response generation.
    used_llm: bool = False

    # Developer/debug visibility.
    llm_usage: dict[str, bool] = Field(
        default_factory=dict
    )

    # fast_path / local_ai / fallback
    execution_mode: str = "unknown"

    # Full end-to-end API request latency.
    response_time_ms: float | None = None

    evidence: Any | None = None

    warnings: list[str] = Field(
        default_factory=list
    )

    analysis_id: str | None = None