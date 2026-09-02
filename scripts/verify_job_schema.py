from __future__ import annotations

from sqlalchemy import text

from backend.app.database import engine


# ============================================================
# OBJECT NAMES
# ============================================================

JOBS_TABLE = (
    "analytics.intelligence_jobs"
)

EVENTS_TABLE = (
    "analytics.intelligence_job_events"
)

JOBS_SEQUENCE = (
    "analytics.intelligence_jobs_job_id_seq"
)

EVENTS_SEQUENCE = (
    "analytics.intelligence_job_events_event_id_seq"
)


# ============================================================
# EXPECTED COLUMNS
# ============================================================

EXPECTED_JOB_COLUMNS = {
    "job_id",
    "job_type",
    "status",
    "stage",
    "progress_pct",
    "requested_by",
    "message",
    "result",
    "error_detail",
    "created_at",
    "started_at",
    "completed_at",
}


EXPECTED_EVENT_COLUMNS = {
    "event_id",
    "job_id",
    "event_type",
    "stage",
    "message",
    "payload",
    "created_at",
}


# ============================================================
# DISPLAY
# ============================================================

def heading(
    title: str,
) -> None:

    print()

    print(
        "="
        *
        72
    )

    print(
        title
    )

    print(
        "="
        *
        72
    )


def check(
    label: str,
    passed: bool,
) -> bool:

    state = (
        "OK"
        if passed
        else
        "FAILED"
    )


    print(
        f"{label:<48} {state}"
    )


    return passed


# ============================================================
# MAIN VERIFICATION
# ============================================================

def verify_job_schema() -> bool:

    failed = False


    with engine.connect() as connection:

        # ====================================================
        # CONNECTION
        # ====================================================

        heading(
            "DATABASE CONNECTION"
        )


        context = (
            connection.execute(
                text(
                    """
                    SELECT
                        current_database()
                            AS database_name,

                        current_user
                            AS current_user,

                        inet_server_addr()::TEXT
                            AS server_address,

                        inet_server_port()
                            AS server_port;
                    """
                )
            )
            .mappings()
            .one()
        )


        print(
            "Database:",
            context[
                "database_name"
            ],
        )

        print(
            "Application user:",
            context[
                "current_user"
            ],
        )

        print(
            "Server address:",
            context[
                "server_address"
            ],
        )

        print(
            "Server port:",
            context[
                "server_port"
            ],
        )


        if (
            context[
                "database_name"
            ]
            !=
            "ai_business_intelligence"
        ):

            failed = True

            print()

            print(
                "ERROR: Application is connected to the wrong database."
            )


        # ====================================================
        # OBJECTS
        # ====================================================

        heading(
            "BACKGROUND JOB OBJECTS"
        )


        objects = (
            connection.execute(
                text(
                    """
                    SELECT
                        TO_REGCLASS(
                            :jobs_table
                        )::TEXT
                            AS jobs_table,

                        TO_REGCLASS(
                            :events_table
                        )::TEXT
                            AS events_table,

                        TO_REGCLASS(
                            :jobs_sequence
                        )::TEXT
                            AS jobs_sequence,

                        TO_REGCLASS(
                            :events_sequence
                        )::TEXT
                            AS events_sequence;
                    """
                ),
                {
                    "jobs_table":
                        JOBS_TABLE,

                    "events_table":
                        EVENTS_TABLE,

                    "jobs_sequence":
                        JOBS_SEQUENCE,

                    "events_sequence":
                        EVENTS_SEQUENCE,
                },
            )
            .mappings()
            .one()
        )


        for label, value in (
            objects.items()
        ):

            if not check(
                label,
                value is not None,
            ):

                failed = True


        if failed:

            heading(
                "FINAL RESULT"
            )

            print(
                "BACKGROUND JOB SCHEMA VALIDATION FAILED"
            )

            print()

            print(
                "Run sql/20260829_background_jobs.sql "
                "as postgres and ensure COMMIT completes."
            )

            return False


        # ====================================================
        # JOB COLUMNS
        # ====================================================

        heading(
            "INTELLIGENCE JOB COLUMNS"
        )


        job_columns = set(
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
                            'intelligence_jobs';
                    """
                )
            )
            .scalars()
            .all()
        )


        for column in sorted(
            EXPECTED_JOB_COLUMNS
        ):

            if not check(
                f"column: {column}",
                column in job_columns,
            ):

                failed = True


        # ====================================================
        # EVENT COLUMNS
        # ====================================================

        heading(
            "INTELLIGENCE JOB EVENT COLUMNS"
        )


        event_columns = set(
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
                            'intelligence_job_events';
                    """
                )
            )
            .scalars()
            .all()
        )


        for column in sorted(
            EXPECTED_EVENT_COLUMNS
        ):

            if not check(
                f"column: {column}",
                column in event_columns,
            ):

                failed = True


        # ====================================================
        # JOB TABLE PRIVILEGES
        # ====================================================

        heading(
            "JOB TABLE PRIVILEGES"
        )


        job_privileges = (
            connection.execute(
                text(
                    """
                    SELECT
                        has_table_privilege(
                            current_user,
                            'analytics.intelligence_jobs',
                            'SELECT'
                        ) AS can_select,

                        has_table_privilege(
                            current_user,
                            'analytics.intelligence_jobs',
                            'INSERT'
                        ) AS can_insert,

                        has_table_privilege(
                            current_user,
                            'analytics.intelligence_jobs',
                            'UPDATE'
                        ) AS can_update,

                        has_table_privilege(
                            current_user,
                            'analytics.intelligence_jobs',
                            'DELETE'
                        ) AS can_delete;
                    """
                )
            )
            .mappings()
            .one()
        )


        for label, value in (
            job_privileges.items()
        ):

            if not check(
                label,
                bool(
                    value
                ),
            ):

                failed = True


        # ====================================================
        # EVENT TABLE PRIVILEGES
        # ====================================================

        heading(
            "EVENT TABLE PRIVILEGES"
        )


        event_privileges = (
            connection.execute(
                text(
                    """
                    SELECT
                        has_table_privilege(
                            current_user,
                            'analytics.intelligence_job_events',
                            'SELECT'
                        ) AS can_select,

                        has_table_privilege(
                            current_user,
                            'analytics.intelligence_job_events',
                            'INSERT'
                        ) AS can_insert,

                        has_table_privilege(
                            current_user,
                            'analytics.intelligence_job_events',
                            'UPDATE'
                        ) AS can_update,

                        has_table_privilege(
                            current_user,
                            'analytics.intelligence_job_events',
                            'DELETE'
                        ) AS can_delete;
                    """
                )
            )
            .mappings()
            .one()
        )


        for label, value in (
            event_privileges.items()
        ):

            if not check(
                label,
                bool(
                    value
                ),
            ):

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
                            'analytics.intelligence_jobs_job_id_seq',
                            'USAGE'
                        ) AS jobs_sequence_usage,

                        has_sequence_privilege(
                            current_user,
                            'analytics.intelligence_job_events_event_id_seq',
                            'USAGE'
                        ) AS events_sequence_usage;
                    """
                )
            )
            .mappings()
            .one()
        )


        for label, value in (
            sequence_privileges.items()
        ):

            if not check(
                label,
                bool(
                    value
                ),
            ):

                failed = True


        # ====================================================
        # FOREIGN KEY
        # ====================================================

        heading(
            "JOB EVENT RELATIONSHIP"
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
                                    'intelligence_job_events'

                                AND
                                constraint_name =
                                    'fk_intelligence_job_events_job'

                                AND
                                constraint_type =
                                    'FOREIGN KEY'
                        );
                    """
                )
            )
            .scalar_one()
        )


        if not check(
            "job_events → intelligence_jobs FK",
            bool(
                foreign_key_exists
            ),
        ):

            failed = True


    # ========================================================
    # FINAL RESULT
    # ========================================================

    heading(
        "FINAL RESULT"
    )


    if failed:

        print(
            "BACKGROUND JOB SCHEMA VALIDATION FAILED"
        )

        return False


    print(
        "BACKGROUND JOB SCHEMA VALIDATION PASSED"
    )

    return True


# ============================================================
# ENTRYPOINT
# ============================================================

def main() -> int:

    try:

        return (
            0
            if verify_job_schema()
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


if __name__ == "__main__":

    raise SystemExit(
        main()
    )