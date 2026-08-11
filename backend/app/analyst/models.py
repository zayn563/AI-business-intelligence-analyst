from datetime import date
from typing import Literal

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
# PARSED INTENT
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
        default=0.5,
        ge=0.0,
        le=1.0,
    )


# ============================================================
# USER REQUEST
# ============================================================

class AnalystAskRequest(BaseModel):

    question: str = Field(
        min_length=3,
        max_length=2000,
    )


# ============================================================
# USER RESPONSE
# ============================================================

class AnalystAskResponse(BaseModel):

    status: str

    question: str

    answer: str

    intent: dict

    parser: str

    tool_used: str

    used_llm: bool

    evidence: dict

    warnings: list[str] = Field(
        default_factory=list
    )