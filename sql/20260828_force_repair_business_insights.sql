-- ============================================================
-- FORCE REPAIR BUSINESS INSIGHTS PERMISSIONS
-- ============================================================
--
-- Execute this entire script as PostgreSQL user: postgres
--
-- Database:
--     ai_business_intelligence
--
-- Application role:
--     ai_analyst_app
--
-- IMPORTANT:
--     Do NOT highlight individual statements.
--     Paste/run the entire script.
-- ============================================================


-- ============================================================
-- 1. MAKE SURE WE ARE NOT IMPERSONATING ANOTHER ROLE
-- ============================================================

RESET ROLE;


-- ============================================================
-- 2. VERIFY DATABASE AND EXECUTION ROLE
-- ============================================================

SELECT
    current_database() AS database_name,
    current_user AS current_user_name,
    session_user AS session_user_name;


-- ============================================================
-- 3. VERIFY ROLE EXISTS
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
            rolname = 'ai_analyst_app'
    )
    THEN

        RAISE EXCEPTION
            'Role ai_analyst_app does not exist.';

    END IF;

END;
$$;


-- ============================================================
-- 4. VERIFY TABLE EXISTS
-- ============================================================

DO
$$
BEGIN

    IF TO_REGCLASS(
        'analytics.business_insights'
    ) IS NULL
    THEN

        RAISE EXCEPTION
            'Table analytics.business_insights does not exist.';

    END IF;

END;
$$;


-- ============================================================
-- 5. VERIFY SEQUENCE EXISTS
-- ============================================================

DO
$$
BEGIN

    IF TO_REGCLASS(
        'analytics.business_insights_insight_id_seq'
    ) IS NULL
    THEN

        RAISE EXCEPTION
            'Sequence analytics.business_insights_insight_id_seq does not exist.';

    END IF;

END;
$$;


-- ============================================================
-- 6. APPLY ALL PERMISSIONS ATOMICALLY
-- ============================================================

BEGIN;


-- ------------------------------------------------------------
-- DATABASE CONNECTION
-- ------------------------------------------------------------

GRANT CONNECT
ON DATABASE ai_business_intelligence
TO ai_analyst_app;


-- ------------------------------------------------------------
-- SCHEMA ACCESS
-- ------------------------------------------------------------

GRANT USAGE
ON SCHEMA analytics
TO ai_analyst_app;


-- ------------------------------------------------------------
-- BUSINESS INSIGHTS TABLE
-- ------------------------------------------------------------

GRANT SELECT
ON TABLE analytics.business_insights
TO ai_analyst_app;


GRANT INSERT
ON TABLE analytics.business_insights
TO ai_analyst_app;


GRANT UPDATE
ON TABLE analytics.business_insights
TO ai_analyst_app;


GRANT DELETE
ON TABLE analytics.business_insights
TO ai_analyst_app;


-- ------------------------------------------------------------
-- BUSINESS INSIGHTS SEQUENCE
-- ------------------------------------------------------------

GRANT USAGE
ON SEQUENCE analytics.business_insights_insight_id_seq
TO ai_analyst_app;


GRANT SELECT
ON SEQUENCE analytics.business_insights_insight_id_seq
TO ai_analyst_app;


GRANT UPDATE
ON SEQUENCE analytics.business_insights_insight_id_seq
TO ai_analyst_app;


-- ------------------------------------------------------------
-- FUTURE ANALYTICS TABLES CREATED BY POSTGRES
-- ------------------------------------------------------------

ALTER DEFAULT PRIVILEGES
FOR ROLE postgres
IN SCHEMA analytics

GRANT
    SELECT,
    INSERT,
    UPDATE,
    DELETE
ON TABLES
TO ai_analyst_app;


-- ------------------------------------------------------------
-- FUTURE ANALYTICS SEQUENCES CREATED BY POSTGRES
-- ------------------------------------------------------------

ALTER DEFAULT PRIVILEGES
FOR ROLE postgres
IN SCHEMA analytics

GRANT
    USAGE,
    SELECT,
    UPDATE
ON SEQUENCES
TO ai_analyst_app;


COMMIT;


-- ============================================================
-- 7. VERIFY SCHEMA PERMISSION
-- ============================================================

SELECT
    has_schema_privilege(
        'ai_analyst_app',
        'analytics',
        'USAGE'
    ) AS schema_usage_allowed;


-- ============================================================
-- 8. VERIFY ALL TABLE PERMISSIONS
-- ============================================================

SELECT
    has_table_privilege(
        'ai_analyst_app',
        'analytics.business_insights',
        'SELECT'
    ) AS select_allowed,

    has_table_privilege(
        'ai_analyst_app',
        'analytics.business_insights',
        'INSERT'
    ) AS insert_allowed,

    has_table_privilege(
        'ai_analyst_app',
        'analytics.business_insights',
        'UPDATE'
    ) AS update_allowed,

    has_table_privilege(
        'ai_analyst_app',
        'analytics.business_insights',
        'DELETE'
    ) AS delete_allowed;


-- ============================================================
-- 9. VERIFY ALL SEQUENCE PERMISSIONS
-- ============================================================

SELECT
    has_sequence_privilege(
        'ai_analyst_app',
        'analytics.business_insights_insight_id_seq',
        'USAGE'
    ) AS sequence_usage_allowed,

    has_sequence_privilege(
        'ai_analyst_app',
        'analytics.business_insights_insight_id_seq',
        'SELECT'
    ) AS sequence_select_allowed,

    has_sequence_privilege(
        'ai_analyst_app',
        'analytics.business_insights_insight_id_seq',
        'UPDATE'
    ) AS sequence_update_allowed;


-- ============================================================
-- 10. SHOW TABLE ACL
-- ============================================================

SELECT
    n.nspname AS schema_name,
    c.relname AS object_name,
    c.relkind AS object_type,
    c.relowner::REGROLE AS owner_name,
    c.relacl AS access_control_list

FROM
    pg_class AS c

INNER JOIN
    pg_namespace AS n
    ON
        n.oid = c.relnamespace

WHERE
    n.nspname = 'analytics'

    AND c.relname IN
    (
        'business_insights',
        'business_insights_insight_id_seq'
    )

ORDER BY
    c.relname;


-- ============================================================
-- 11. SHOW INFORMATION-SCHEMA GRANTS
-- ============================================================

SELECT
    grantee,
    privilege_type

FROM
    information_schema.role_table_grants

WHERE
    table_schema = 'analytics'

    AND table_name = 'business_insights'

    AND grantee = 'ai_analyst_app'

ORDER BY
    privilege_type;


-- ============================================================
-- 12. HARD VALIDATION
-- ============================================================
--
-- The script itself will fail here if permissions were not
-- successfully granted.
-- ============================================================

DO
$$
BEGIN

    IF NOT has_table_privilege(
        'ai_analyst_app',
        'analytics.business_insights',
        'SELECT'
    )
    THEN

        RAISE EXCEPTION
            'SELECT permission was not granted.';

    END IF;


    IF NOT has_table_privilege(
        'ai_analyst_app',
        'analytics.business_insights',
        'INSERT'
    )
    THEN

        RAISE EXCEPTION
            'INSERT permission was not granted.';

    END IF;


    IF NOT has_table_privilege(
        'ai_analyst_app',
        'analytics.business_insights',
        'UPDATE'
    )
    THEN

        RAISE EXCEPTION
            'UPDATE permission was not granted.';

    END IF;


    IF NOT has_table_privilege(
        'ai_analyst_app',
        'analytics.business_insights',
        'DELETE'
    )
    THEN

        RAISE EXCEPTION
            'DELETE permission was not granted.';

    END IF;


    IF NOT has_sequence_privilege(
        'ai_analyst_app',
        'analytics.business_insights_insight_id_seq',
        'USAGE'
    )
    THEN

        RAISE EXCEPTION
            'Sequence USAGE permission was not granted.';

    END IF;


    RAISE NOTICE
        'SUCCESS: ai_analyst_app permissions are correctly configured.';

END;
$$;