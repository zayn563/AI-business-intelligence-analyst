-- ==========================================================
-- BUSINESS INSIGHT PERSISTENCE
-- ==========================================================
--
-- Creates the persistent business-insight store used by:
--
-- - priority lifecycle management
-- - NEW / ONGOING / ESCALATED / RESOLVED tracking
-- - investigation workspace
-- - morning business brief
--
-- This script should be executed by PostgreSQL administrator
-- or the owner of the analytics schema objects.
-- ==========================================================


-- ==========================================================
-- TABLE
-- ==========================================================

CREATE TABLE IF NOT EXISTS analytics.business_insights
(
    insight_id BIGSERIAL PRIMARY KEY,

    fingerprint TEXT NOT NULL UNIQUE,

    title TEXT NOT NULL,

    insight_type TEXT NOT NULL,

    dimension TEXT NOT NULL,

    dimension_value TEXT NOT NULL,

    primary_metric TEXT NOT NULL,

    diagnosis TEXT,

    severity TEXT NOT NULL,

    priority_score NUMERIC(12, 2) NOT NULL,

    lifecycle_status TEXT NOT NULL,

    period_start DATE NOT NULL,

    period_end DATE NOT NULL,

    comparison_start DATE NOT NULL,

    comparison_end DATE NOT NULL,

    first_detected_at TIMESTAMPTZ
        NOT NULL
        DEFAULT NOW(),

    last_detected_at TIMESTAMPTZ
        NOT NULL
        DEFAULT NOW(),

    resolved_at TIMESTAMPTZ,

    occurrence_count INTEGER
        NOT NULL
        DEFAULT 1,

    payload JSONB
        NOT NULL
        DEFAULT '{}'::JSONB,

    created_at TIMESTAMPTZ
        NOT NULL
        DEFAULT NOW(),

    updated_at TIMESTAMPTZ
        NOT NULL
        DEFAULT NOW(),

    CONSTRAINT business_insights_type_check
        CHECK
        (
            insight_type IN
            (
                'risk',
                'opportunity'
            )
        ),

    CONSTRAINT business_insights_status_check
        CHECK
        (
            lifecycle_status IN
            (
                'NEW',
                'ONGOING',
                'ESCALATED',
                'RESOLVED'
            )
        )
);


-- ==========================================================
-- INDEXES
-- ==========================================================

CREATE INDEX IF NOT EXISTS
    idx_business_insights_status
ON
    analytics.business_insights
    (
        lifecycle_status
    );


CREATE INDEX IF NOT EXISTS
    idx_business_insights_priority
ON
    analytics.business_insights
    (
        priority_score DESC
    );


CREATE INDEX IF NOT EXISTS
    idx_business_insights_dimension
ON
    analytics.business_insights
    (
        dimension,
        dimension_value
    );


CREATE INDEX IF NOT EXISTS
    idx_business_insights_last_detected
ON
    analytics.business_insights
    (
        last_detected_at DESC
    );


-- ==========================================================
-- APPLICATION ROLE PERMISSIONS
-- ==========================================================

GRANT USAGE
ON SCHEMA analytics
TO ai_analyst_app;


GRANT
    SELECT,
    INSERT,
    UPDATE,
    DELETE
ON TABLE
    analytics.business_insights
TO
    ai_analyst_app;


GRANT
    USAGE,
    SELECT,
    UPDATE
ON SEQUENCE
    analytics.business_insights_insight_id_seq
TO
    ai_analyst_app;


-- ==========================================================
-- DEFAULT PRIVILEGES
-- ==========================================================
--
-- Future tables / sequences created by postgres in analytics
-- will automatically receive application-role permissions.
-- ==========================================================

ALTER DEFAULT PRIVILEGES
FOR ROLE postgres
IN SCHEMA analytics

GRANT
    SELECT,
    INSERT,
    UPDATE,
    DELETE
ON TABLES
TO
    ai_analyst_app;


ALTER DEFAULT PRIVILEGES
FOR ROLE postgres
IN SCHEMA analytics

GRANT
    USAGE,
    SELECT,
    UPDATE
ON SEQUENCES
TO
    ai_analyst_app;