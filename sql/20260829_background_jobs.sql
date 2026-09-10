-- ============================================================
-- AI BUSINESS INTELLIGENCE ANALYST
-- BACKGROUND INTELLIGENCE JOB ENGINE
-- ============================================================
--
-- Database:
--     ai_business_intelligence
--
-- Execute as:
--     postgres
--
-- IMPORTANT:
--
-- This migration explicitly uses BEGIN / COMMIT.
--
-- Therefore the objects remain persisted even if pgAdmin's
-- Auto Commit option is disabled.
--
-- Run the ENTIRE script using F5 / Execute Script.
-- Do not highlight individual statements.
--
-- ============================================================


-- ============================================================
-- 1. RESET PREVIOUS ROLE
-- ============================================================

RESET ROLE;


-- ============================================================
-- 2. VERIFY DATABASE CONTEXT BEFORE MIGRATION
-- ============================================================

SELECT
    current_database() AS database_name,
    current_user AS current_user_name,
    session_user AS session_user_name,
    inet_server_addr() AS server_address,
    inet_server_port() AS server_port,
    current_setting(
        'data_directory'
    ) AS postgres_data_directory;


-- ============================================================
-- 3. ENSURE WE ARE RUNNING AGAINST THE CORRECT DATABASE
-- ============================================================

DO
$$

BEGIN

    IF current_database()
        <>
        'ai_business_intelligence'
    THEN

        RAISE EXCEPTION
            'Wrong database. Expected ai_business_intelligence but connected to %.',
            current_database();

    END IF;

END;

$$;


-- ============================================================
-- 4. BEGIN EXPLICIT TRANSACTION
-- ============================================================

BEGIN;


-- ============================================================
-- 5. VERIFY ANALYTICS SCHEMA
-- ============================================================

DO
$$

BEGIN

    IF NOT EXISTS
    (
        SELECT
            1

        FROM
            pg_namespace

        WHERE
            nspname =
                'analytics'
    )
    THEN

        RAISE EXCEPTION
            'Required schema analytics does not exist.';

    END IF;

END;

$$;


-- ============================================================
-- 6. VERIFY APPLICATION ROLE
-- ============================================================

DO
$$

BEGIN

    IF NOT EXISTS
    (
        SELECT
            1

        FROM
            pg_roles

        WHERE
            rolname =
                'ai_analyst_app'
    )
    THEN

        RAISE EXCEPTION
            'Required PostgreSQL role ai_analyst_app does not exist.';

    END IF;

END;

$$;


-- ============================================================
-- 7. CREATE INTELLIGENCE JOBS TABLE
-- ============================================================

CREATE TABLE IF NOT EXISTS
    analytics.intelligence_jobs
(
    job_id BIGSERIAL PRIMARY KEY,

    job_type TEXT NOT NULL,

    status TEXT
        NOT NULL
        DEFAULT 'QUEUED',

    stage TEXT
        NOT NULL
        DEFAULT 'QUEUED',

    progress_pct INTEGER
        NOT NULL
        DEFAULT 0,

    requested_by TEXT
        NOT NULL
        DEFAULT 'frontend',

    message TEXT,

    result JSONB,

    error_detail TEXT,

    created_at TIMESTAMPTZ
        NOT NULL
        DEFAULT NOW(),

    started_at TIMESTAMPTZ,

    completed_at TIMESTAMPTZ,

    CONSTRAINT intelligence_jobs_type_check
        CHECK
        (
            job_type IN
            (
                'ANALYZE_ONLY',
                'REFRESH_AND_ANALYZE'
            )
        ),

    CONSTRAINT intelligence_jobs_status_check
        CHECK
        (
            status IN
            (
                'QUEUED',
                'RUNNING',
                'COMPLETED',
                'FAILED'
            )
        ),

    CONSTRAINT intelligence_jobs_stage_check
        CHECK
        (
            stage IN
            (
                'QUEUED',
                'REFRESHING',
                'ANALYZING',
                'COMPLETED',
                'FAILED'
            )
        ),

    CONSTRAINT intelligence_jobs_progress_check
        CHECK
        (
            progress_pct >= 0

            AND

            progress_pct <= 100
        )
);


-- ============================================================
-- 8. CREATE INTELLIGENCE JOB EVENTS TABLE
-- ============================================================

CREATE TABLE IF NOT EXISTS
    analytics.intelligence_job_events
(
    event_id BIGSERIAL PRIMARY KEY,

    job_id BIGINT NOT NULL,

    event_type TEXT NOT NULL,

    stage TEXT NOT NULL,

    message TEXT NOT NULL,

    payload JSONB,

    created_at TIMESTAMPTZ
        NOT NULL
        DEFAULT NOW(),

    CONSTRAINT fk_intelligence_job_events_job
        FOREIGN KEY
        (
            job_id
        )
        REFERENCES
            analytics.intelligence_jobs
            (
                job_id
            )
        ON DELETE CASCADE
);


-- ============================================================
-- 9. JOB STATUS INDEX
-- ============================================================

CREATE INDEX IF NOT EXISTS
    idx_intelligence_jobs_status

ON
    analytics.intelligence_jobs
    (
        status
    );


-- ============================================================
-- 10. JOB TYPE INDEX
-- ============================================================

CREATE INDEX IF NOT EXISTS
    idx_intelligence_jobs_type

ON
    analytics.intelligence_jobs
    (
        job_type
    );


-- ============================================================
-- 11. JOB CREATED-AT INDEX
-- ============================================================

CREATE INDEX IF NOT EXISTS
    idx_intelligence_jobs_created

ON
    analytics.intelligence_jobs
    (
        created_at DESC
    );


-- ============================================================
-- 12. JOB EVENTS LOOKUP INDEX
-- ============================================================

CREATE INDEX IF NOT EXISTS
    idx_intelligence_job_events_job

ON
    analytics.intelligence_job_events
    (
        job_id,
        created_at
    );


-- ============================================================
-- 13. GRANT ANALYTICS SCHEMA ACCESS
-- ============================================================

GRANT USAGE
ON SCHEMA
    analytics
TO
    ai_analyst_app;


-- ============================================================
-- 14. GRANT JOB TABLE ACCESS
-- ============================================================

GRANT
    SELECT,
    INSERT,
    UPDATE,
    DELETE

ON TABLE
    analytics.intelligence_jobs

TO
    ai_analyst_app;


-- ============================================================
-- 15. GRANT EVENT TABLE ACCESS
-- ============================================================

GRANT
    SELECT,
    INSERT,
    UPDATE,
    DELETE

ON TABLE
    analytics.intelligence_job_events

TO
    ai_analyst_app;


-- ============================================================
-- 16. GRANT JOB SEQUENCE ACCESS
-- ============================================================

GRANT
    USAGE,
    SELECT,
    UPDATE

ON SEQUENCE
    analytics.intelligence_jobs_job_id_seq

TO
    ai_analyst_app;


-- ============================================================
-- 17. GRANT EVENT SEQUENCE ACCESS
-- ============================================================

GRANT
    USAGE,
    SELECT,
    UPDATE

ON SEQUENCE
    analytics.intelligence_job_events_event_id_seq

TO
    ai_analyst_app;


-- ============================================================
-- 18. DEFAULT FUTURE TABLE PRIVILEGES
-- ============================================================

ALTER DEFAULT PRIVILEGES
FOR ROLE
    postgres
IN SCHEMA
    analytics

GRANT
    SELECT,
    INSERT,
    UPDATE,
    DELETE

ON TABLES

TO
    ai_analyst_app;


-- ============================================================
-- 19. DEFAULT FUTURE SEQUENCE PRIVILEGES
-- ============================================================

ALTER DEFAULT PRIVILEGES
FOR ROLE
    postgres
IN SCHEMA
    analytics

GRANT
    USAGE,
    SELECT,
    UPDATE

ON SEQUENCES

TO
    ai_analyst_app;


-- ============================================================
-- 20. VERIFY OBJECTS BEFORE COMMIT
-- ============================================================

DO
$$

BEGIN

    IF TO_REGCLASS(
        'analytics.intelligence_jobs'
    ) IS NULL
    THEN

        RAISE EXCEPTION
            'analytics.intelligence_jobs was not created.';

    END IF;


    IF TO_REGCLASS(
        'analytics.intelligence_job_events'
    ) IS NULL
    THEN

        RAISE EXCEPTION
            'analytics.intelligence_job_events was not created.';

    END IF;


    IF TO_REGCLASS(
        'analytics.intelligence_jobs_job_id_seq'
    ) IS NULL
    THEN

        RAISE EXCEPTION
            'analytics.intelligence_jobs_job_id_seq was not created.';

    END IF;


    IF TO_REGCLASS(
        'analytics.intelligence_job_events_event_id_seq'
    ) IS NULL
    THEN

        RAISE EXCEPTION
            'analytics.intelligence_job_events_event_id_seq was not created.';

    END IF;

END;

$$;


-- ============================================================
-- 21. VERIFY APPLICATION PRIVILEGES BEFORE COMMIT
-- ============================================================

DO
$$

BEGIN

    IF NOT has_table_privilege(
        'ai_analyst_app',
        'analytics.intelligence_jobs',
        'SELECT'
    )
    THEN

        RAISE EXCEPTION
            'ai_analyst_app lacks SELECT on intelligence_jobs.';

    END IF;


    IF NOT has_table_privilege(
        'ai_analyst_app',
        'analytics.intelligence_jobs',
        'INSERT'
    )
    THEN

        RAISE EXCEPTION
            'ai_analyst_app lacks INSERT on intelligence_jobs.';

    END IF;


    IF NOT has_table_privilege(
        'ai_analyst_app',
        'analytics.intelligence_jobs',
        'UPDATE'
    )
    THEN

        RAISE EXCEPTION
            'ai_analyst_app lacks UPDATE on intelligence_jobs.';

    END IF;


    IF NOT has_table_privilege(
        'ai_analyst_app',
        'analytics.intelligence_jobs',
        'DELETE'
    )
    THEN

        RAISE EXCEPTION
            'ai_analyst_app lacks DELETE on intelligence_jobs.';

    END IF;


    IF NOT has_table_privilege(
        'ai_analyst_app',
        'analytics.intelligence_job_events',
        'SELECT'
    )
    THEN

        RAISE EXCEPTION
            'ai_analyst_app lacks SELECT on intelligence_job_events.';

    END IF;


    IF NOT has_table_privilege(
        'ai_analyst_app',
        'analytics.intelligence_job_events',
        'INSERT'
    )
    THEN

        RAISE EXCEPTION
            'ai_analyst_app lacks INSERT on intelligence_job_events.';

    END IF;


    IF NOT has_sequence_privilege(
        'ai_analyst_app',
        'analytics.intelligence_jobs_job_id_seq',
        'USAGE'
    )
    THEN

        RAISE EXCEPTION
            'ai_analyst_app lacks USAGE on intelligence_jobs sequence.';

    END IF;


    IF NOT has_sequence_privilege(
        'ai_analyst_app',
        'analytics.intelligence_job_events_event_id_seq',
        'USAGE'
    )
    THEN

        RAISE EXCEPTION
            'ai_analyst_app lacks USAGE on intelligence_job_events sequence.';

    END IF;

END;

$$;


-- ============================================================
-- 22. COMMIT MIGRATION
-- ============================================================

COMMIT;


-- ============================================================
-- EVERYTHING BELOW THIS POINT RUNS AFTER COMMIT
-- ============================================================


-- ============================================================
-- 23. VERIFY TRANSACTION IS NO LONGER OPEN
-- ============================================================

SELECT
    current_database() AS database_name,
    current_user AS current_user_name;


-- ============================================================
-- 24. POST-COMMIT OBJECT VERIFICATION
-- ============================================================

SELECT
    TO_REGCLASS(
        'analytics.intelligence_jobs'
    ) AS jobs_table,

    TO_REGCLASS(
        'analytics.intelligence_jobs_job_id_seq'
    ) AS jobs_sequence,

    TO_REGCLASS(
        'analytics.intelligence_job_events'
    ) AS events_table,

    TO_REGCLASS(
        'analytics.intelligence_job_events_event_id_seq'
    ) AS events_sequence;


-- ============================================================
-- 25. POST-COMMIT TABLE PRIVILEGES
-- ============================================================

SELECT
    has_table_privilege(
        'ai_analyst_app',
        'analytics.intelligence_jobs',
        'SELECT'
    ) AS jobs_select,

    has_table_privilege(
        'ai_analyst_app',
        'analytics.intelligence_jobs',
        'INSERT'
    ) AS jobs_insert,

    has_table_privilege(
        'ai_analyst_app',
        'analytics.intelligence_jobs',
        'UPDATE'
    ) AS jobs_update,

    has_table_privilege(
        'ai_analyst_app',
        'analytics.intelligence_jobs',
        'DELETE'
    ) AS jobs_delete,

    has_table_privilege(
        'ai_analyst_app',
        'analytics.intelligence_job_events',
        'SELECT'
    ) AS events_select,

    has_table_privilege(
        'ai_analyst_app',
        'analytics.intelligence_job_events',
        'INSERT'
    ) AS events_insert,

    has_table_privilege(
        'ai_analyst_app',
        'analytics.intelligence_job_events',
        'UPDATE'
    ) AS events_update,

    has_table_privilege(
        'ai_analyst_app',
        'analytics.intelligence_job_events',
        'DELETE'
    ) AS events_delete;


-- ============================================================
-- 26. POST-COMMIT SEQUENCE PRIVILEGES
-- ============================================================

SELECT
    has_sequence_privilege(
        'ai_analyst_app',
        'analytics.intelligence_jobs_job_id_seq',
        'USAGE'
    ) AS jobs_sequence_usage,

    has_sequence_privilege(
        'ai_analyst_app',
        'analytics.intelligence_job_events_event_id_seq',
        'USAGE'
    ) AS events_sequence_usage;


-- ============================================================
-- 27. VERIFY COLUMNS
-- ============================================================

SELECT
    table_name,
    ordinal_position,
    column_name,
    data_type,
    is_nullable,
    column_default

FROM
    information_schema.columns

WHERE
    table_schema =
        'analytics'

    AND
    table_name IN
    (
        'intelligence_jobs',
        'intelligence_job_events'
    )

ORDER BY
    table_name,
    ordinal_position;


-- ============================================================
-- 28. FINAL POST-COMMIT VALIDATION
-- ============================================================

DO
$$

BEGIN

    IF TO_REGCLASS(
        'analytics.intelligence_jobs'
    ) IS NULL
    THEN

        RAISE EXCEPTION
            'POST-COMMIT FAILURE: intelligence_jobs does not exist.';

    END IF;


    IF TO_REGCLASS(
        'analytics.intelligence_job_events'
    ) IS NULL
    THEN

        RAISE EXCEPTION
            'POST-COMMIT FAILURE: intelligence_job_events does not exist.';

    END IF;


    RAISE NOTICE
        'SUCCESS: background intelligence job schema is committed and persistent.';

END;

$$;