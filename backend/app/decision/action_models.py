from __future__ import annotations

from datetime import date

from typing import Literal

from pydantic import (
    BaseModel,
    Field,
)


# ============================================================
# ACTION STATUS
# ============================================================

ActionStatus = Literal[
    "OPEN",
    "IN_PROGRESS",
    "BLOCKED",
    "COMPLETED",
]


# ============================================================
# CREATE ACTION
# ============================================================

class ActionCreateRequest(
    BaseModel
):

    title: str = Field(
        min_length=3,
        max_length=200,
    )

    owner: str | None = Field(
        default=None,
        max_length=120,
    )

    due_date: date | None = None

    notes: str | None = Field(
        default=None,
        max_length=2000,
    )


# ============================================================
# UPDATE ACTION
# ============================================================

class ActionUpdateRequest(
    BaseModel
):

    title: str | None = Field(
        default=None,
        min_length=3,
        max_length=200,
    )

    owner: str | None = Field(
        default=None,
        max_length=120,
    )

    status: ActionStatus | None = None

    due_date: date | None = None

    notes: str | None = Field(
        default=None,
        max_length=2000,
    )