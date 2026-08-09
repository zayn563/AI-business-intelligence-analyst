from datetime import date
from enum import Enum
from typing import Any, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from .metrics import (
    SUPPORTED_DIMENSIONS,
    SUPPORTED_METRICS,
)


# ============================================================
# ANALYSIS TYPES
# ============================================================

class AnalysisType(str, Enum):
    summary = "summary"
    breakdown = "breakdown"
    ranking = "ranking"
    trend = "trend"
    comparison = "comparison"


# ============================================================
# DATE RANGE
# ============================================================

class DateRange(BaseModel):

    model_config = ConfigDict(
        extra="forbid"
    )

    start: date
    end: date

    @model_validator(mode="after")
    def validate_dates(self):

        if self.end < self.start:
            raise ValueError(
                "End date cannot be before start date."
            )

        return self


# ============================================================
# ANALYSIS FILTERS
# ============================================================

class AnalysisFilters(BaseModel):

    model_config = ConfigDict(
        extra="forbid"
    )

    region: str | None = None
    city: str | None = None
    channel: str | None = None
    store: str | None = None
    product: str | None = None
    brand: str | None = None
    category: str | None = None
    subcategory: str | None = None
    salesperson: str | None = None


# ============================================================
# ANALYSIS REQUEST
# ============================================================

class AnalysisRequest(BaseModel):

    model_config = ConfigDict(
        extra="forbid"
    )

    analysis_type: AnalysisType

    metrics: list[str] = Field(
        min_length=1
    )

    dimension: str | None = None

    filters: AnalysisFilters = Field(
        default_factory=AnalysisFilters
    )

    period: DateRange

    comparison_period: DateRange | None = None

    top_n: int = Field(
        default=5,
        ge=1,
        le=100,
    )

    sort_direction: Literal[
        "asc",
        "desc",
    ] = "desc"

    # --------------------------------------------------------
    # METRIC VALIDATION
    # --------------------------------------------------------

    @field_validator("metrics")
    @classmethod
    def validate_metrics(
        cls,
        metrics: list[str],
    ) -> list[str]:

        invalid = [
            metric
            for metric in metrics
            if metric not in SUPPORTED_METRICS
        ]

        if invalid:
            raise ValueError(
                f"Unsupported metrics: {invalid}"
            )

        return metrics

    # --------------------------------------------------------
    # REQUEST VALIDATION
    # --------------------------------------------------------

    @model_validator(mode="after")
    def validate_request(self):

        if (
            self.dimension is not None
            and self.dimension not in SUPPORTED_DIMENSIONS
        ):
            raise ValueError(
                f"Unsupported dimension: "
                f"{self.dimension}"
            )

        if self.analysis_type in {
            AnalysisType.breakdown,
            AnalysisType.ranking,
            AnalysisType.trend,
        }:
            if self.dimension is None:
                raise ValueError(
                    "This analysis type "
                    "requires a dimension."
                )

        if (
            self.analysis_type == AnalysisType.comparison
            and self.comparison_period is None
        ):
            raise ValueError(
                "Comparison analysis requires "
                "comparison_period."
            )

        return self


# ============================================================
# SEMANTIC MAPPING REQUEST
# ============================================================

class SemanticMappingRequest(BaseModel):

    model_config = ConfigDict(
        extra="forbid"
    )

    columns: list[str] = Field(
        min_length=1
    )

    sample_rows: list[
        dict[str, Any]
    ] = Field(
        default_factory=list
    )

    max_sample_values: int = Field(
        default=5,
        ge=1,
        le=20,
    )

    @field_validator("columns")
    @classmethod
    def validate_columns(
        cls,
        columns: list[str],
    ) -> list[str]:

        cleaned = [
            column.strip()
            for column in columns
            if column.strip()
        ]

        if not cleaned:
            raise ValueError(
                "At least one valid column is required."
            )

        if len(cleaned) != len(set(cleaned)):
            raise ValueError(
                "Duplicate source column names "
                "are not supported."
            )

        return cleaned


# ============================================================
# SOURCE ENUMS
# ============================================================

class SourceType(str, Enum):
    csv = "csv"
    google_sheets = "google_sheets"


class LoadStrategy(str, Enum):
    append = "append"
    upsert = "upsert"


# ============================================================
# CREATE DATA SOURCE
# ============================================================

class DataSourceCreate(BaseModel):

    model_config = ConfigDict(
        extra="forbid"
    )

    source_name: str = Field(
        min_length=1,
        max_length=200,
    )

    source_type: SourceType

    source_location: str = Field(
        min_length=1
    )

    sheet_name: str | None = None

    is_active: bool = True

    load_strategy: LoadStrategy = LoadStrategy.upsert


# ============================================================
# UPDATE DATA SOURCE
# ============================================================

class DataSourceUpdate(BaseModel):

    model_config = ConfigDict(
        extra="forbid"
    )

    source_name: str | None = None

    source_location: str | None = None

    sheet_name: str | None = None

    is_active: bool | None = None

    load_strategy: LoadStrategy | None = None