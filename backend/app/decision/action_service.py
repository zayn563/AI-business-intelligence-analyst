from __future__ import annotations

from sqlalchemy import text

from ..database import engine

from .action_models import (
    ActionCreateRequest,
    ActionUpdateRequest,
)


# ============================================================
# SERIALIZATION
# ============================================================

def serialize_action(
    row,
) -> dict:

    result = dict(
        row
    )

    return {
        "action_id":
            result[
                "action_id"
            ],

        "insight_id":
            result[
                "insight_id"
            ],

        "title":
            result[
                "title"
            ],

        "owner":
            result.get(
                "owner_name"
            ),

        "status":
            result[
                "status"
            ],

        "due_date":
            result.get(
                "due_date"
            ),

        "notes":
            result.get(
                "notes"
            ),

        "created_at":
            result.get(
                "created_at"
            ),

        "updated_at":
            result.get(
                "updated_at"
            ),

        "completed_at":
            result.get(
                "completed_at"
            ),
    }


# ============================================================
# VERIFY INSIGHT
# ============================================================

def ensure_insight_exists(
    connection,
    insight_id: int,
) -> None:

    exists = (
        connection.execute(
            text(
                """
                SELECT
                    EXISTS
                    (
                        SELECT
                            1
                        FROM
                            analytics.business_insights
                        WHERE
                            insight_id =
                                :insight_id
                    );
                """
            ),
            {
                "insight_id":
                    insight_id,
            },
        )
        .scalar_one()
    )

    if not exists:

        raise ValueError(
            f"Insight {insight_id} was not found."
        )


# ============================================================
# LIST ACTIONS
# ============================================================

def list_insight_actions(
    insight_id: int,
) -> list[dict]:

    with engine.connect() as connection:

        ensure_insight_exists(
            connection,
            insight_id,
        )

        rows = (
            connection.execute(
                text(
                    """
                    SELECT
                        *
                    FROM
                        analytics.insight_actions
                    WHERE
                        insight_id =
                            :insight_id
                    ORDER BY
                        CASE
                            WHEN status = 'BLOCKED'
                                THEN 0
                            WHEN status = 'IN_PROGRESS'
                                THEN 1
                            WHEN status = 'OPEN'
                                THEN 2
                            ELSE 3
                        END,
                        due_date NULLS LAST,
                        created_at DESC;
                    """
                ),
                {
                    "insight_id":
                        insight_id,
                },
            )
            .mappings()
            .all()
        )

    return [
        serialize_action(
            row
        )
        for row
        in rows
    ]


# ============================================================
# CREATE ACTION
# ============================================================

def create_insight_action(
    insight_id: int,
    request: ActionCreateRequest,
) -> dict:

    with engine.begin() as connection:

        ensure_insight_exists(
            connection,
            insight_id,
        )

        row = (
            connection.execute(
                text(
                    """
                    INSERT INTO
                        analytics.insight_actions
                    (
                        insight_id,
                        title,
                        owner_name,
                        status,
                        due_date,
                        notes
                    )
                    VALUES
                    (
                        :insight_id,
                        :title,
                        :owner_name,
                        'OPEN',
                        :due_date,
                        :notes
                    )
                    RETURNING
                        *;
                    """
                ),
                {
                    "insight_id":
                        insight_id,

                    "title":
                        request.title,

                    "owner_name":
                        request.owner,

                    "due_date":
                        request.due_date,

                    "notes":
                        request.notes,
                },
            )
            .mappings()
            .one()
        )

    return serialize_action(
        row
    )


# ============================================================
# UPDATE ACTION
# ============================================================

def update_action(
    action_id: int,
    request: ActionUpdateRequest,
) -> dict:

    with engine.begin() as connection:

        existing = (
            connection.execute(
                text(
                    """
                    SELECT
                        *
                    FROM
                        analytics.insight_actions
                    WHERE
                        action_id =
                            :action_id;
                    """
                ),
                {
                    "action_id":
                        action_id,
                },
            )
            .mappings()
            .first()
        )

        if existing is None:

            raise ValueError(
                f"Action {action_id} was not found."
            )

        existing_dict = dict(
            existing
        )

        changes = request.model_dump(
            exclude_unset=True
        )

        title = (
            changes.get(
                "title"
            )
            or
            existing_dict[
                "title"
            ]
        )

        owner_name = (
            changes[
                "owner"
            ]
            if
            "owner"
            in changes
            else
            existing_dict.get(
                "owner_name"
            )
        )

        status = (
            changes.get(
                "status"
            )
            or
            existing_dict[
                "status"
            ]
        )

        due_date = (
            changes[
                "due_date"
            ]
            if
            "due_date"
            in changes
            else
            existing_dict.get(
                "due_date"
            )
        )

        notes = (
            changes[
                "notes"
            ]
            if
            "notes"
            in changes
            else
            existing_dict.get(
                "notes"
            )
        )

        row = (
            connection.execute(
                text(
                    """
                    UPDATE
                        analytics.insight_actions

                    SET
                        title =
                            :title,

                        owner_name =
                            :owner_name,

                        status =
                            :status,

                        due_date =
                            :due_date,

                        notes =
                            :notes,

                        completed_at =
                            CASE
                                WHEN
                                    :status
                                    =
                                    'COMPLETED'
                                THEN
                                    COALESCE(
                                        completed_at,
                                        NOW()
                                    )
                                ELSE
                                    NULL
                            END,

                        updated_at =
                            NOW()

                    WHERE
                        action_id =
                            :action_id

                    RETURNING
                        *;
                    """
                ),
                {
                    "action_id":
                        action_id,

                    "title":
                        title,

                    "owner_name":
                        owner_name,

                    "status":
                        status,

                    "due_date":
                        due_date,

                    "notes":
                        notes,
                },
            )
            .mappings()
            .one()
        )

    return serialize_action(
        row
    )


# ============================================================
# DELETE ACTION
# ============================================================

def delete_action(
    action_id: int,
) -> dict:

    with engine.begin() as connection:

        deleted = (
            connection.execute(
                text(
                    """
                    DELETE FROM
                        analytics.insight_actions
                    WHERE
                        action_id =
                            :action_id
                    RETURNING
                        action_id;
                    """
                ),
                {
                    "action_id":
                        action_id,
                },
            )
            .scalar_one_or_none()
        )

    if deleted is None:

        raise ValueError(
            f"Action {action_id} was not found."
        )

    return {
        "status":
            "deleted",

        "action_id":
            deleted,
    }