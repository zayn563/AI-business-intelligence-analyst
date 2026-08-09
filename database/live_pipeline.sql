-- ============================================================
-- LIVE DATA PIPELINE
-- AI BUSINESS INTELLIGENCE ANALYST
-- ============================================================


-- ============================================================
-- 1. DATA SOURCE REGISTRY
-- ============================================================

CREATE TABLE IF NOT EXISTS analytics.data_sources (

    source_id BIGSERIAL PRIMARY KEY,

    source_name VARCHAR(200) NOT NULL UNIQUE,

    source_type VARCHAR(50) NOT NULL
        CHECK (
            source_type IN (
                'csv',
                'google_sheets'
            )
        ),

    source_location TEXT NOT NULL,

    sheet_name VARCHAR(200),

    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    load_strategy VARCHAR(30) NOT NULL DEFAULT 'upsert'
        CHECK (
            load_strategy IN (
                'append',
                'upsert'
            )
        ),

    mapping_status VARCHAR(30) NOT NULL DEFAULT 'pending'
        CHECK (
            mapping_status IN (
                'pending',
                'ready',
                'review_required',
                'error'
            )
        ),

    schema_fingerprint VARCHAR(64),

    last_successful_refresh TIMESTAMPTZ,

    last_refresh_status VARCHAR(30),

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


-- ============================================================
-- 2. SAVED SOURCE → CANONICAL FIELD MAPPINGS
-- ============================================================

CREATE TABLE IF NOT EXISTS analytics.source_column_mappings (

    mapping_id BIGSERIAL PRIMARY KEY,

    source_id BIGINT NOT NULL
        REFERENCES analytics.data_sources(source_id)
        ON DELETE CASCADE,

    source_column TEXT NOT NULL,

    normalized_source_column TEXT NOT NULL,

    canonical_field TEXT,

    confidence NUMERIC(6,4),

    mapping_method VARCHAR(50),

    mapping_status VARCHAR(50),

    is_confirmed BOOLEAN NOT NULL DEFAULT FALSE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (
        source_id,
        source_column
    )
);


-- ============================================================
-- 3. REFRESH HISTORY / AUDIT
-- ============================================================

CREATE TABLE IF NOT EXISTS analytics.data_refresh_runs (

    refresh_id BIGSERIAL PRIMARY KEY,

    source_id BIGINT NOT NULL
        REFERENCES analytics.data_sources(source_id)
        ON DELETE CASCADE,

    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    finished_at TIMESTAMPTZ,

    status VARCHAR(30) NOT NULL
        CHECK (
            status IN (
                'running',
                'success',
                'failed'
            )
        ),

    schema_changed BOOLEAN,

    rows_read BIGINT NOT NULL DEFAULT 0,

    rows_inserted BIGINT NOT NULL DEFAULT 0,

    rows_updated BIGINT NOT NULL DEFAULT 0,

    rows_unchanged BIGINT NOT NULL DEFAULT 0,

    rows_rejected BIGINT NOT NULL DEFAULT 0,

    error_message TEXT,

    details JSONB NOT NULL DEFAULT '{}'::jsonb
);


-- ============================================================
-- 4. SOURCE RECORD STATE
--
-- Stores the last hash seen for each source/business record.
-- This gives us change tracking and auditability without
-- adding technical columns to fact_sales_daily.
-- ============================================================

CREATE TABLE IF NOT EXISTS analytics.source_record_state (

    source_id BIGINT NOT NULL
        REFERENCES analytics.data_sources(source_id)
        ON DELETE CASCADE,

    source_record_key TEXT NOT NULL,

    record_hash VARCHAR(64) NOT NULL,

    first_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    last_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    PRIMARY KEY (
        source_id,
        source_record_key
    )
);


-- ============================================================
-- INDEXES
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_data_sources_active
ON analytics.data_sources(is_active);


CREATE INDEX IF NOT EXISTS idx_source_mappings_source
ON analytics.source_column_mappings(source_id);


CREATE INDEX IF NOT EXISTS idx_refresh_runs_source
ON analytics.data_refresh_runs(source_id);


CREATE INDEX IF NOT EXISTS idx_refresh_runs_started
ON analytics.data_refresh_runs(started_at DESC);


CREATE INDEX IF NOT EXISTS idx_record_state_source
ON analytics.source_record_state(source_id);