-- ==========================================================
-- BUSINESS INSIGHTS PERMISSION REPAIR
-- ==========================================================
--
-- IMPORTANT
-- Run this file using PostgreSQL administrator / object owner.
--
-- Recommended:
--     current_user = postgres
--
-- Do NOT run this while SET ROLE ai_analyst_app is active.
-- ==========================================================


-- ==========================================================
-- 1. ENSURE WE ARE NOT USING A PREVIOUS SET ROLE
-- ==========================================================

RESET ROLE;


-- ==========================================================
-- 2. DISPLAY CURRENT EXECUTION USER
-- ==========================================================

SELECT
    current_user AS execution_user,
    session_user AS session_user;


-- ==========================================================
-- 3. CONFIRM APPLICATION ROLE EXISTS
-- ==========================================================

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
            rolname = 'ai_analyst_app'
    )
    THEN

        RAISE EXCEPTION
            'Role ai_analyst_app does not exist.';

    END IF;

END;

$$;


-- ==========================================================
-- 4. CONFIRM TABLE EXISTS
-- ==========================================================

DO
$$

BEGIN

    IF TO_REGCLASS(
        'analytics.business_insights'
    ) IS NULL
    THEN

        RAISE EXCEPTION
            'analytics.business_insights does not exist.';

    END IF;

END;

$$;


-- ==========================================================
-- 5. SCHEMA ACCESS
-- ==========================================================

GRANT USAGE
ON SCHEMA analytics
TO ai_analyst_app;


-- ==========================================================
-- 6. TABLE ACCESS
-- ==========================================================

GRANT
    SELECT,
    INSERT,
    UPDATE,
    DELETE
ON TABLE
    analytics.business_insights
TO
    ai_analyst_app;


-- ==========================================================
-- 7. SEQUENCE ACCESS
-- ==========================================================
--
-- BIGSERIAL creates:
--
-- analytics.business_insights_insight_id_seq
--
-- INSERT requires access to this sequence.
-- ==========================================================

GRANT
    USAGE,
    SELECT,
    UPDATE
ON SEQUENCE
    analytics.business_insights_insight_id_seq
TO
    ai_analyst_app;


-- ==========================================================
-- 8. VERIFY SCHEMA ACCESS
-- ==========================================================

SELECT
    has_schema_privilege(
        'ai_analyst_app',
        'analytics',
        'USAGE'
    )
    AS schema_usage_allowed;


-- ==========================================================
-- 9. VERIFY TABLE ACCESS
-- ==========================================================

SELECT
    has_table_privilege(
        'ai_analyst_app',
        'analytics.business_insights',
        'SELECT'
    )
    AS select_allowed,

    has_table_privilege(
        'ai_analyst_app',
        'analytics.business_insights',
        'INSERT'
    )
    AS insert_allowed,

    has_table_privilege(
        'ai_analyst_app',
        'analytics.business_insights',
        'UPDATE'
    )
    AS update_allowed,

    has_table_privilege(
        'ai_analyst_app',
        'analytics.business_insights',
        'DELETE'
    )
    AS delete_allowed;


-- ==========================================================
-- 10. VERIFY SEQUENCE ACCESS
-- ==========================================================

SELECT
    has_sequence_privilege(
        'ai_analyst_app',
        'analytics.business_insights_insight_id_seq',
        'USAGE'
    )
    AS sequence_usage_allowed,

    has_sequence_privilege(
        'ai_analyst_app',
        'analytics.business_insights_insight_id_seq',
        'SELECT'
    )
    AS sequence_select_allowed,

    has_sequence_privilege(
        'ai_analyst_app',
        'analytics.business_insights_insight_id_seq',
        'UPDATE'
    )
    AS sequence_update_allowed;


-- ==========================================================
-- 11. DISPLAY ACTUAL GRANTS
-- ==========================================================

SELECT
    grantee,
    privilege_type

FROM
    information_schema.role_table_grants

WHERE
    table_schema = 'analytics'

    AND
    table_name = 'business_insights'

    AND
    grantee = 'ai_analyst_app'

ORDER BY
    privilege_type;


-- ==========================================================
-- END
-- ==========================================================