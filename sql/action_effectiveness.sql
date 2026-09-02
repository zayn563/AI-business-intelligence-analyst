BEGIN;


-- ============================================================
-- ACTION EFFECTIVENESS / OUTCOME TRACKING
-- ============================================================
--
-- PURPOSE
-- -------
-- Stores observed KPI movement after a tracked management
-- action.
--
-- IMPORTANT
-- ---------
-- This table records association / observed outcome.
-- It does NOT claim causal attribution.
--
-- causality_claimed therefore defaults to FALSE.
-- ============================================================


-- ============================================================
-- SAFETY CHECK
--
-- Prevent accidentally creating this schema in another
-- PostgreSQL database.
-- ============================================================

DO
$$
BEGIN

    IF
        CURRENT_DATABASE()
        <>
        'ai_business_intelligence'
    THEN

        RAISE EXCEPTION
            'Wrong database. Expected ai_business_intelligence but connected to %.',
            CURRENT_DATABASE();

    END IF;

END
$$;


-- ============================================================
-- TABLE
-- ============================================================

CREATE TABLE IF NOT EXISTS
    analytics.action_effectiveness_evaluations
(
    evaluation_id
        BIGSERIAL
        PRIMARY KEY,

    action_id
        BIGINT
        NOT NULL,

    insight_id
        BIGINT
        NOT NULL,

    evaluated_at
        TIMESTAMPTZ
        NOT NULL
        DEFAULT NOW(),

    baseline_start
        DATE
        NOT NULL,

    baseline_end
        DATE
        NOT NULL,

    evaluation_start
        DATE
        NOT NULL,

    evaluation_end
        DATE
        NOT NULL,

    primary_metric
        TEXT
        NOT NULL,

    dimension
        TEXT
        NOT NULL,

    dimension_value
        TEXT,

    baseline_value
        NUMERIC(24, 6),

    current_value
        NUMERIC(24, 6),

    absolute_change
        NUMERIC(24, 6),

    change_pct
        NUMERIC(24, 6),

    change_pp
        NUMERIC(24, 6),

    desired_direction
        TEXT
        NOT NULL,

    effectiveness_status
        TEXT
        NOT NULL,

    evaluation_basis
        TEXT
        NOT NULL
        DEFAULT
        'insight_period_to_latest_full_month',

    causality_claimed
        BOOLEAN
        NOT NULL
        DEFAULT FALSE,

    summary
        TEXT
        NOT NULL,

    evidence
        JSONB
        NOT NULL
        DEFAULT '{}'::JSONB,

    created_at
        TIMESTAMPTZ
        NOT NULL
        DEFAULT NOW(),

    CONSTRAINT
        action_effectiveness_action_fk
        FOREIGN KEY
        (
            action_id
        )
        REFERENCES
            analytics.insight_actions
            (
                action_id
            )
        ON DELETE CASCADE,

    CONSTRAINT
        action_effectiveness_insight_fk
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

    CONSTRAINT
        action_effectiveness_direction_check
        CHECK
        (
            desired_direction
            IN
            (
                'INCREASE',
                'DECREASE',
                'MAINTAIN'
            )
        ),

    CONSTRAINT
        action_effectiveness_status_check
        CHECK
        (
            effectiveness_status
            IN
            (
                'IMPROVED',
                'UNCHANGED',
                'WORSENED'
            )
        ),

    CONSTRAINT
        action_effectiveness_period_check
        CHECK
        (
            baseline_start
            <=
            baseline_end

            AND

            evaluation_start
            <=
            evaluation_end
        ),

    CONSTRAINT
        action_effectiveness_unique_evaluation
        UNIQUE
        (
            action_id,
            evaluation_end,
            primary_metric
        )
);


-- ============================================================
-- INDEXES
-- ============================================================

CREATE INDEX IF NOT EXISTS
    idx_action_effectiveness_action
ON
    analytics.action_effectiveness_evaluations
    (
        action_id
    );


CREATE INDEX IF NOT EXISTS
    idx_action_effectiveness_insight
ON
    analytics.action_effectiveness_evaluations
    (
        insight_id
    );


CREATE INDEX IF NOT EXISTS
    idx_action_effectiveness_evaluated_at
ON
    analytics.action_effectiveness_evaluations
    (
        evaluated_at DESC
    );


CREATE INDEX IF NOT EXISTS
    idx_action_effectiveness_status
ON
    analytics.action_effectiveness_evaluations
    (
        effectiveness_status
    );


-- ============================================================
-- APPLICATION PERMISSIONS
-- ============================================================

GRANT
    SELECT,
    INSERT,
    UPDATE,
    DELETE
ON
    analytics.action_effectiveness_evaluations
TO
    ai_analyst_app;


GRANT
    USAGE,
    SELECT
ON SEQUENCE
    analytics.action_effectiveness_evaluations_evaluation_id_seq
TO
    ai_analyst_app;


COMMIT;


-- ============================================================
-- POST-COMMIT DATABASE CHECK
-- ============================================================

SELECT
    CURRENT_DATABASE()
        AS current_database,

    CURRENT_USER
        AS current_user;


-- ============================================================
-- POST-COMMIT TABLE CHECK
-- ============================================================

SELECT
    TO_REGCLASS(
        'analytics.action_effectiveness_evaluations'
    )
        AS action_effectiveness_table;


-- ============================================================
-- POST-COMMIT COLUMN CHECK
-- ============================================================

SELECT
    column_name,
    data_type,
    is_nullable

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