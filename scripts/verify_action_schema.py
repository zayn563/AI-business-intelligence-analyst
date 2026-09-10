from __future__ import annotations

from sqlalchemy import text

from backend.app.database import engine


# ============================================================
# CONSTANTS
# ============================================================

ACTION_TABLE = (
    "analytics.insight_actions"
)

ACTION_SEQUENCE = (
    "analytics.insight_actions_action_id_seq"
)

EXPECTED_COLUMNS = {
    "action_id",
    "insight_id",
    "title",
    "owner_name",
    "status",
    "due_date",
    "notes",
    "created_at",
    "updated_at",
    "completed_at",
}


# ============================================================
# DISPLAY HELPERS
# ============================================================

def heading(
    value: str,
) -> None:

    print()

    print(
        "="
        *
        72
    )

    print(
        value
    )

    print(
        "="
        *
        72
    )


def print_check(
    label: str,
    passed: bool,
) -> None:

    status = (
        "OK"
        if passed
        else
        "FAILED"
    )

    print(
        f"{label:<42} {status}"
    )


# ============================================================
# VERIFY ACTION SCHEMA
# ============================================================

def verify_action_schema() -> bool:

    failed = False


    with engine.connect() as connection:

        # ====================================================
        # DATABASE CONNECTION
        # ====================================================

        heading(
            "DATABASE CONNECTION"
        )


        connection_info = (
            connection.execute(
                text(
                    """
                    SELECT
                        current_database()
                            AS database_name,

                        current_user
                            AS current_user;
                    """
                )
            )
            .mappings()
            .one()
        )


        print(
            "Database:",
            connection_info[
                "database_name"
            ],
        )

        print(
            "Application user:",
            connection_info[
                "current_user"
            ],
        )


        # ====================================================
        # OBJECT EXISTENCE
        # ====================================================

        heading(
            "ACTION SCHEMA OBJECTS"
        )


        objects = (
            connection.execute(
                text(
                    """
                    SELECT
                        TO_REGCLASS(
                            :table_name
                        )::TEXT
                            AS table_name,

                        TO_REGCLASS(
                            :sequence_name
                        )::TEXT
                            AS sequence_name;
                    """
                ),
                {
                    "table_name":
                        ACTION_TABLE,

                    "sequence_name":
                        ACTION_SEQUENCE,
                },
            )
            .mappings()
            .one()
        )


        table_exists = (
            objects[
                "table_name"
            ]
            is not None
        )

        sequence_exists = (
            objects[
                "sequence_name"
            ]
            is not None
        )


        print_check(
            "insight_actions table",
            table_exists,
        )

        print_check(
            "action_id sequence",
            sequence_exists,
        )


        if not table_exists:

            failed = True


        if not sequence_exists:

            failed = True


        if failed:

            heading(
                "FINAL RESULT"
            )

            print(
                "ACTION SCHEMA VALIDATION FAILED"
            )

            return False


        # ====================================================
        # TABLE COLUMNS
        # ====================================================

        heading(
            "TABLE COLUMNS"
        )


        columns = (
            connection.execute(
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
                            'insight_actions'

                    ORDER BY
                        ordinal_position;
                    """
                )
            )
            .scalars()
            .all()
        )


        actual_columns = set(
            columns
        )


        for column in sorted(
            EXPECTED_COLUMNS
        ):

            exists = (
                column
                in
                actual_columns
            )

            print_check(
                f"column: {column}",
                exists,
            )

            if not exists:

                failed = True


        # ====================================================
        # SCHEMA PRIVILEGE
        # ====================================================

        heading(
            "SCHEMA PRIVILEGES"
        )


        schema_usage = (
            connection.execute(
                text(
                    """
                    SELECT
                        has_schema_privilege(
                            current_user,
                            'analytics',
                            'USAGE'
                        );
                    """
                )
            )
            .scalar_one()
        )


        print_check(
            "analytics schema USAGE",
            bool(
                schema_usage
            ),
        )


        if not schema_usage:

            failed = True


        # ====================================================
        # TABLE PRIVILEGES
        # ====================================================

        heading(
            "TABLE PRIVILEGES"
        )


        privileges = (
            connection.execute(
                text(
                    """
                    SELECT
                        has_table_privilege(
                            current_user,
                            'analytics.insight_actions',
                            'SELECT'
                        ) AS can_select,

                        has_table_privilege(
                            current_user,
                            'analytics.insight_actions',
                            'INSERT'
                        ) AS can_insert,

                        has_table_privilege(
                            current_user,
                            'analytics.insight_actions',
                            'UPDATE'
                        ) AS can_update,

                        has_table_privilege(
                            current_user,
                            'analytics.insight_actions',
                            'DELETE'
                        ) AS can_delete;
                    """
                )
            )
            .mappings()
            .one()
        )


        for label, value in (
            privileges.items()
        ):

            passed = bool(
                value
            )

            print_check(
                label,
                passed,
            )

            if not passed:

                failed = True


        # ====================================================
        # SEQUENCE PRIVILEGES
        # ====================================================

        heading(
            "SEQUENCE PRIVILEGES"
        )


        sequence_privileges = (
            connection.execute(
                text(
                    """
                    SELECT
                        has_sequence_privilege(
                            current_user,
                            'analytics.insight_actions_action_id_seq',
                            'USAGE'
                        ) AS can_use_sequence,

                        has_sequence_privilege(
                            current_user,
                            'analytics.insight_actions_action_id_seq',
                            'SELECT'
                        ) AS can_select_sequence,

                        has_sequence_privilege(
                            current_user,
                            'analytics.insight_actions_action_id_seq',
                            'UPDATE'
                        ) AS can_update_sequence;
                    """
                )
            )
            .mappings()
            .one()
        )


        for label, value in (
            sequence_privileges.items()
        ):

            passed = bool(
                value
            )

            print_check(
                label,
                passed,
            )

            if not passed:

                failed = True


        # ====================================================
        # FOREIGN KEY
        # ====================================================

        heading(
            "RELATIONSHIP VALIDATION"
        )


        foreign_key_exists = (
            connection.execute(
                text(
                    """
                    SELECT
                        EXISTS
                        (
                            SELECT
                                1

                            FROM
                                information_schema.table_constraints

                            WHERE
                                table_schema =
                                    'analytics'

                                AND
                                table_name =
                                    'insight_actions'

                                AND
                                constraint_name =
                                    'fk_insight_actions_insight'

                                AND
                                constraint_type =
                                    'FOREIGN KEY'
                        );
                    """
                )
            )
            .scalar_one()
        )


        print_check(
            (
                "business_insights "
                "foreign key"
            ),
            bool(
                foreign_key_exists
            ),
        )


        if not foreign_key_exists:

            failed = True


        # ====================================================
        # STATUS CONSTRAINT
        # ====================================================

        heading(
            "STATUS CONSTRAINT"
        )


        status_constraint_exists = (
            connection.execute(
                text(
                    """
                    SELECT
                        EXISTS
                        (
                            SELECT
                                1

                            FROM
                                information_schema.table_constraints

                            WHERE
                                table_schema =
                                    'analytics'

                                AND
                                table_name =
                                    'insight_actions'

                                AND
                                constraint_name =
                                    'insight_actions_status_check'

                                AND
                                constraint_type =
                                    'CHECK'
                        );
                    """
                )
            )
            .scalar_one()
        )


        print_check(
            "action status check",
            bool(
                status_constraint_exists
            ),
        )


        if not status_constraint_exists:

            failed = True


    # ========================================================
    # FINAL RESULT
    # ========================================================

    heading(
        "FINAL RESULT"
    )


    if failed:

        print(
            "ACTION SCHEMA VALIDATION FAILED"
        )

        return False


    print(
        "ACTION SCHEMA VALIDATION PASSED"
    )

    return True


# ============================================================
# MAIN
# ============================================================

def main() -> int:

    try:

        passed = (
            verify_action_schema()
        )

        return (
            0
            if passed
            else
            1
        )

    except Exception as error:

        heading(
            "UNEXPECTED ERROR"
        )

        print(
            type(
                error
            ).__name__
        )

        print(
            str(
                error
            )
        )

        return 1


# ============================================================
# ENTRYPOINT
# ============================================================

if __name__ == "__main__":

    raise SystemExit(
        main()
    )