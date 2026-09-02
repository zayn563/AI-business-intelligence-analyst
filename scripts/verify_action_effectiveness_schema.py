from __future__ import annotations

import sys

from pathlib import Path


# ============================================================
# PROJECT ROOT
# ============================================================

PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[1]
)


if (
    str(
        PROJECT_ROOT
    )
    not in
    sys.path
):

    sys.path.insert(
        0,
        str(
            PROJECT_ROOT
        ),
    )


# ============================================================
# IMPORTS
# ============================================================

from sqlalchemy import text

from backend.app.database import engine


# ============================================================
# EXPECTED COLUMNS
# ============================================================

EXPECTED_COLUMNS = {
    "evaluation_id",
    "action_id",
    "insight_id",
    "evaluated_at",
    "baseline_start",
    "baseline_end",
    "evaluation_start",
    "evaluation_end",
    "primary_metric",
    "dimension",
    "dimension_value",
    "baseline_value",
    "current_value",
    "absolute_change",
    "change_pct",
    "change_pp",
    "desired_direction",
    "effectiveness_status",
    "evaluation_basis",
    "causality_claimed",
    "summary",
    "evidence",
    "created_at",
}


# ============================================================
# MAIN
# ============================================================

def main() -> int:

    print()

    print(
        "="
        *
        72
    )

    print(
        "ACTION EFFECTIVENESS SCHEMA VERIFICATION"
    )

    print(
        "="
        *
        72
    )

    with engine.connect() as connection:

        database_name = (
            connection
            .execute(
                text(
                    """
                    SELECT
                        CURRENT_DATABASE();
                    """
                )
            )
            .scalar_one()
        )

        current_user = (
            connection
            .execute(
                text(
                    """
                    SELECT
                        CURRENT_USER;
                    """
                )
            )
            .scalar_one()
        )

        relation = (
            connection
            .execute(
                text(
                    """
                    SELECT
                        TO_REGCLASS(
                            'analytics.action_effectiveness_evaluations'
                        );
                    """
                )
            )
            .scalar_one_or_none()
        )

        print()

        print(
            f"Database:    {database_name}"
        )

        print(
            f"User:        {current_user}"
        )

        if relation is None:

            print()

            print(
                "FAILED"
            )

            print(
                (
                    "analytics.action_effectiveness_evaluations "
                    "does not exist."
                )
            )

            print()

            print(
                "FIX:"
            )

            print(
                (
                    "1. Open sql/action_effectiveness.sql "
                    "in pgAdmin Query Tool."
                )
            )

            print(
                (
                    "2. Confirm the database is "
                    "ai_business_intelligence."
                )
            )

            print(
                (
                    "3. Execute the COMPLETE script "
                    "with F5."
                )
            )

            print(
                (
                    "4. Run this verification command "
                    "again."
                )
            )

            return 1

        rows = (
            connection
            .execute(
                text(
                    """
                    SELECT
                        column_name

                    FROM
                        information_schema.columns

                    WHERE
                        table_schema =
                            'analytics'

                        AND

                        table_name =
                            'action_effectiveness_evaluations'

                    ORDER BY
                        ordinal_position;
                    """
                )
            )
            .scalars()
            .all()
        )

        existing_columns = set(
            rows
        )

        missing_columns = (
            EXPECTED_COLUMNS
            -
            existing_columns
        )

        select_privilege = (
            connection
            .execute(
                text(
                    """
                    SELECT
                        HAS_TABLE_PRIVILEGE(
                            CURRENT_USER,
                            'analytics.action_effectiveness_evaluations',
                            'SELECT'
                        );
                    """
                )
            )
            .scalar_one()
        )

        insert_privilege = (
            connection
            .execute(
                text(
                    """
                    SELECT
                        HAS_TABLE_PRIVILEGE(
                            CURRENT_USER,
                            'analytics.action_effectiveness_evaluations',
                            'INSERT'
                        );
                    """
                )
            )
            .scalar_one()
        )

        update_privilege = (
            connection
            .execute(
                text(
                    """
                    SELECT
                        HAS_TABLE_PRIVILEGE(
                            CURRENT_USER,
                            'analytics.action_effectiveness_evaluations',
                            'UPDATE'
                        );
                    """
                )
            )
            .scalar_one()
        )

        delete_privilege = (
            connection
            .execute(
                text(
                    """
                    SELECT
                        HAS_TABLE_PRIVILEGE(
                            CURRENT_USER,
                            'analytics.action_effectiveness_evaluations',
                            'DELETE'
                        );
                    """
                )
            )
            .scalar_one()
        )

        sequence_privilege = (
            connection
            .execute(
                text(
                    """
                    SELECT
                        HAS_SEQUENCE_PRIVILEGE(
                            CURRENT_USER,
                            'analytics.action_effectiveness_evaluations_evaluation_id_seq',
                            'USAGE'
                        );
                    """
                )
            )
            .scalar_one()
        )

    print()

    print(
        f"Table:       {relation}"
    )

    print(
        f"Columns:     {len(existing_columns)}"
    )

    print(
        f"SELECT:      {select_privilege}"
    )

    print(
        f"INSERT:      {insert_privilege}"
    )

    print(
        f"UPDATE:      {update_privilege}"
    )

    print(
        f"DELETE:      {delete_privilege}"
    )

    print(
        f"SEQ USAGE:   {sequence_privilege}"
    )

    if missing_columns:

        print()

        print(
            "FAILED"
        )

        print(
            "Missing columns:"
        )

        for column in sorted(
            missing_columns
        ):

            print(
                f" - {column}"
            )

        return 1

    privileges_ok = all(
        (
            select_privilege,
            insert_privilege,
            update_privilege,
            delete_privilege,
            sequence_privilege,
        )
    )

    if not privileges_ok:

        print()

        print(
            (
                "FAILED: required application "
                "privileges are missing."
            )
        )

        return 1

    print()

    print(
        "SUCCESS"
    )

    print(
        (
            "Action Effectiveness schema is "
            "present, committed and accessible."
        )
    )

    return 0


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    raise SystemExit(
        main()
    )