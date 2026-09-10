from pydantic import (
    BaseModel,
    Field,
)


# ============================================================
# SCENARIO REQUEST
# ============================================================

class ScenarioRequest(BaseModel):

    insight_id: int | None = None

    volume_change_pct: float = Field(
        default=0.0,
        ge=-50.0,
        le=100.0,
    )

    list_price_change_pct: float = Field(
        default=0.0,
        ge=-30.0,
        le=50.0,
    )

    discount_rate_change_pp: float = Field(
        default=0.0,
        ge=-30.0,
        le=30.0,
    )

    cost_per_unit_change_pct: float = Field(
        default=0.0,
        ge=-50.0,
        le=100.0,
    )