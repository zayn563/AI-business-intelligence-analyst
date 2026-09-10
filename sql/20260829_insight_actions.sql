-- ============================================================
-- AI BUSINESS INTELLIGENCE ANALYST
-- INSIGHT ACTION TRACKING
-- ============================================================
--
-- Database:
--     ai_business_intelligence
--
-- Execute as:
--     postgres
--
-- This migration explicitly COMMITs its DDL.
--
-- ============================================================


RESET ROLE;


-- ============================================================
-- VERIFY DATABASE
-- ============================================================

SELECT
    current_database() AS database_name,
    current_user AS current_user_name,
    session_user AS session_user_name,
    inet_server_addr() AS server_address,
    inet_server_port() AS server_port;


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
-- START MIGRATION
-- ============================================================

BEGIN;


-- ============================================================
-- REQUIRED PARENT TABLE
-- ============================================================

DO
$$

BEGIN

    IF TO_REGCLASS(
        'analytics.business_insights'
    ) IS NULL
    THEN

        RAISE EXCEPTION
            'Required table analytics.business_insights does not exist.';

    END IF;

END;

$$;


-- ============================================================
-- CREATE ACTION TABLE
-- ============================================================

CREATE TABLE IF NOT EXISTS
    analytics.insight_actions
(
    action_id BIGSERIAL PRIMARY KEY,

    insight_id BIGINT NOT NULL,

    title TEXT NOT NULL,

    owner_name TEXT,

    status TEXT
        NOT NULL
        DEFAULT 'OPEN',

    due_date DATE,

    notes TEXT,

    created_at TIMESTAMPTZ
        NOT NULL
        DEFAULT NOW(),

    updated_at TIMESTAMPTZ
        NOT NULL
        DEFAULT NOW(),

    completed_at TIMESTAMPTZ,

    CONSTRAINT fk_insight_actions_insight
        FOREIGN KEY
        (
            insight_id
        )
        REFERENCES
            analytics.business_insights
            (
                insight_id
            )
        ON DELETE CASCADE,

    CONSTRAINT insight_actions_status_check
        CHECK
        (
            status IN
            (
                'OPEN',
                'IN_PROGRESS',
                'BLOCKED',
                'COMPLETED'
            )
        )
);


-- ============================================================
-- INDEXES
-- ============================================================

CREATE INDEX IF NOT EXISTS
    idx_insight_actions_insight

ON
    analytics.insight_actions
    (
        insight_id
    );


CREATE INDEX IF NOT EXISTS
    idx_insight_actions_status

ON
    analytics.insight_actions
    (
        status
    );


CREATE INDEX IF NOT EXISTS
    idx_insight_actions_due_date

ON
    analytics.insight_actions
    (
        due_date
    );


-- ============================================================
-- PRIVILEGES
-- ============================================================

GRANT USAGE
ON SCHEMA
    analytics
TO
    ai_analyst_app;


GRANT
    SELECT,
    INSERT,
    UPDATE,
    DELETE

ON TABLE
    analytics.insight_actions

TO
    ai_analyst_app;


GRANT
    USAGE,
    SELECT,
    UPDATE

ON SEQUENCE
    analytics.insight_actions_action_id_seq

TO
    ai_analyst_app;


-- ============================================================
-- VERIFY BEFORE COMMIT
-- ============================================================

DO
$$

BEGIN

    IF TO_REGCLASS(
        'analytics.insight_actions'
    ) IS NULL
    THEN

        RAISE EXCEPTION
            'analytics.insight_actions was not created.';

    END IF;


    IF NOT has_table_privilege(
        'ai_analyst_app',
        'analytics.insight_actions',
        'INSERT'
    )
    THEN

        RAISE EXCEPTION
            'ai_analyst_app lacks INSERT permission.';

    END IF;


    IF NOT has_table_privilege(
        'ai_analyst_app',
        'analytics.insight_actions',
        'UPDATE'
    )
    THEN

        RAISE EXCEPTION
            'ai_analyst_app lacks UPDATE permission.';

    END IF;


    IF NOT has_sequence_privilege(
        'ai_analyst_app',
        'analytics.insight_actions_action_id_seq',
        'USAGE'
    )
    THEN

        RAISE EXCEPTION
            'ai_analyst_app lacks sequence USAGE permission.';

    END IF;

END;

$$;


-- ============================================================
-- COMMIT
-- ============================================================

COMMIT;


-- ============================================================
-- POST-COMMIT VERIFICATION
-- ============================================================

SELECT
    TO_REGCLASS(
        'analytics.insight_actions'
    ) AS table_name,

    TO_REGCLASS(
        'analytics.insight_actions_action_id_seq'
    ) AS sequence_name;


SELECT
    has_table_privilege(
        'ai_analyst_app',
        'analytics.insight_actions',
        'SELECT'
    ) AS can_select,

    has_table_privilege(
        'ai_analyst_app',
        'analytics.insight_actions',
        'INSERT'
    ) AS can_insert,

    has_table_privilege(
        'ai_analyst_app',
        'analytics.insight_actions',
        'UPDATE'
    ) AS can_update,

    has_table_privilege(
        'ai_analyst_app',
        'analytics.insight_actions',
        'DELETE'
    ) AS can_delete,

    has_sequence_privilege(
        'ai_analyst_app',
        'analytics.insight_actions_action_id_seq',
        'USAGE'
    ) AS can_use_sequence;


DO
$$

BEGIN

    IF TO_REGCLASS(
        'analytics.insight_actions'
    ) IS NULL
    THEN

        RAISE EXCEPTION
            'POST-COMMIT FAILURE: insight_actions does not exist.';

    END IF;


    RAISE NOTICE
        'SUCCESS: insight_actions schema is committed and persistent.';

END;

$$;