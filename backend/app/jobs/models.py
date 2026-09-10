from __future__ import annotations

from typing import Literal

from pydantic import (
    BaseModel,
    Field,
)


# ============================================================
# JOB TYPES
# ============================================================

JobType = Literal[
    "ANALYZE_ONLY",
    "REFRESH_AND_ANALYZE",
]


JobStatus = Literal[
    "QUEUED",
    "RUNNING",
    "COMPLETED",
    "FAILED",
]


JobStage = Literal[
    "QUEUED",
    "REFRESHING",
    "ANALYZING",
    "COMPLETED",
    "FAILED",
]


# ============================================================
# CREATE JOB REQUEST
# ============================================================

class IntelligenceJobCreateRequest(
    BaseModel
):

    job_type: JobType

    requested_by: str = Field(
        default="frontend",
        min_length=1,
        max_length=100,
    )