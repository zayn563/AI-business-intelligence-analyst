from datetime import date
from typing import Literal

from pydantic import (
    BaseModel,
    Field,
    model_validator,
)


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
# PERIOD
# ============================================================

class PeriodRange(BaseModel):

    start: date
    end: date

    @model_validator(
        mode="after"
    )
    def validate_dates(
        self,
    ):

        if self.start > self.end:

            raise ValueError(
                "Period start cannot be after period end."
            )

        return self


# ============================================================
# INTELLIGENCE REQUEST
# ============================================================

class IntelligenceRunRequest(BaseModel):

    current_period: (
        PeriodRange | None
    ) = None

    comparison_period: (
        PeriodRange | None
    ) = None

    dimensions: list[
        DimensionName
    ] = Field(
        default_factory=lambda: [
            "region",
            "category",
            "channel",
            "product",
        ]
    )

    metrics: list[
        MetricName
    ] = Field(
        default_factory=lambda: [
            "net_sales",
            "units_sold",
            "gross_profit",
            "margin_pct",
            "avg_selling_price",
            "discount_pct",
            "stockout_rate",
        ]
    )

    top_n: int = Field(
        default=20,
        ge=1,
        le=100,
    )

    @model_validator(
        mode="after"
    )
    def validate_period_pair(
        self,
    ):

        current_exists = (
            self.current_period
            is not None
        )

        comparison_exists = (
            self.comparison_period
            is not None
        )

        if (
            current_exists
            !=
            comparison_exists
        ):

            raise ValueError(
                "Provide both current_period and "
                "comparison_period, or provide neither."
            )

        return self