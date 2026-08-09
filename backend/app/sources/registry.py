import json

from sqlalchemy import text

from ..database import engine


# ============================================================
# ROW HELPER
# ============================================================

def _row_to_dict(
    row,
):

    if row is None:
        return None

    return dict(
        row._mapping
    )


# ============================================================
# CREATE SOURCE
# ============================================================

def create_source(
    data: dict,
) -> dict:

    sql = text(
        """
        INSERT INTO analytics.data_sources (
            source_name,
            source_type,
            source_location,
            sheet_name,
            is_active,
            load_strategy
        )
        VALUES (
            :source_name,
            :source_type,
            :source_location,
            :sheet_name,
            :is_active,
            :load_strategy
        )
        RETURNING *;
        """
    )


    with engine.begin() as connection:

        row = connection.execute(
            sql,
            data,
        ).fetchone()


    return _row_to_dict(
        row
    )


# ============================================================
# LIST SOURCES
# ============================================================

def list_sources() -> list[dict]:

    sql = text(
        """
        SELECT *
        FROM analytics.data_sources
        ORDER BY source_id;
        """
    )


    with engine.connect() as connection:

        rows = (
            connection.execute(
                sql
            )
            .fetchall()
        )


    return [
        _row_to_dict(
            row
        )
        for row
        in rows
    ]


# ============================================================
# GET SOURCE
# ============================================================

def get_source(
    source_id: int,
) -> dict | None:

    sql = text(
        """
        SELECT *
        FROM analytics.data_sources
        WHERE source_id = :source_id;
        """
    )


    with engine.connect() as connection:

        row = connection.execute(
            sql,
            {
                "source_id":
                    source_id
            },
        ).fetchone()


    return _row_to_dict(
        row
    )


# ============================================================
# UPDATE SOURCE
# ============================================================

def update_source(
    source_id: int,
    changes: dict,
) -> dict | None:

    allowed_fields = {
        "source_name",
        "source_location",
        "sheet_name",
        "is_active",
        "load_strategy",
    }


    clean_changes = {

        key:
            value

        for key, value
        in changes.items()

        if (
            key in allowed_fields
            and value is not None
        )
    }


    if not clean_changes:

        return get_source(
            source_id
        )


    set_parts = [

        f"{field} = :{field}"

        for field
        in clean_changes
    ]


    set_parts.append(
        "updated_at = NOW()"
    )


    sql = text(
        f"""
        UPDATE analytics.data_sources
        SET
            {", ".join(set_parts)}
        WHERE
            source_id = :source_id
        RETURNING *;
        """
    )


    params = {
        **clean_changes,
        "source_id":
            source_id,
    }


    with engine.begin() as connection:

        row = connection.execute(
            sql,
            params,
        ).fetchone()


    return _row_to_dict(
        row
    )


# ============================================================
# UPDATE SCHEMA / MAPPING STATE
# ============================================================

def update_source_schema_state(
    source_id: int,
    fingerprint: str,
    mapping_status: str,
):

    sql = text(
        """
        UPDATE analytics.data_sources
        SET
            schema_fingerprint =
                :schema_fingerprint,

            mapping_status =
                :mapping_status,

            updated_at =
                NOW()

        WHERE
            source_id =
                :source_id;
        """
    )


    with engine.begin() as connection:

        connection.execute(
            sql,
            {
                "source_id":
                    source_id,

                "schema_fingerprint":
                    fingerprint,

                "mapping_status":
                    mapping_status,
            },
        )


# ============================================================
# GET SAVED COLUMN MAPPINGS
# ============================================================

def get_source_mappings(
    source_id: int,
) -> list[dict]:

    sql = text(
        """
        SELECT
            source_column,
            normalized_source_column,
            canonical_field,
            confidence,
            mapping_method,
            mapping_status,
            is_confirmed

        FROM analytics.source_column_mappings

        WHERE
            source_id = :source_id

        ORDER BY
            mapping_id;
        """
    )


    with engine.connect() as connection:

        rows = (
            connection.execute(
                sql,
                {
                    "source_id":
                        source_id
                },
            )
            .fetchall()
        )


    return [

        _row_to_dict(
            row
        )

        for row
        in rows
    ]


# ============================================================
# REPLACE SOURCE MAPPINGS
# ============================================================

def replace_source_mappings(
    source_id: int,
    mappings: list[dict],
):

    delete_sql = text(
        """
        DELETE FROM analytics.source_column_mappings
        WHERE source_id = :source_id;
        """
    )


    insert_sql = text(
        """
        INSERT INTO analytics.source_column_mappings (
            source_id,
            source_column,
            normalized_source_column,
            canonical_field,
            confidence,
            mapping_method,
            mapping_status,
            is_confirmed
        )
        VALUES (
            :source_id,
            :source_column,
            :normalized_source_column,
            :canonical_field,
            :confidence,
            :mapping_method,
            :mapping_status,
            :is_confirmed
        );
        """
    )


    payload = []


    for mapping in mappings:

        payload.append(
            {
                "source_id":
                    source_id,

                "source_column":
                    mapping[
                        "source_column"
                    ],

                "normalized_source_column":
                    mapping[
                        "normalized_column"
                    ],

                "canonical_field":
                    mapping.get(
                        "canonical_field"
                    ),

                "confidence":
                    mapping.get(
                        "confidence"
                    ),

                "mapping_method":
                    mapping.get(
                        "method"
                    ),

                "mapping_status":
                    mapping.get(
                        "status"
                    ),

                "is_confirmed":
                    mapping.get(
                        "is_confirmed",
                        False,
                    ),
            }
        )


    with engine.begin() as connection:

        connection.execute(
            delete_sql,
            {
                "source_id":
                    source_id
            },
        )


        if payload:

            connection.execute(
                insert_sql,
                payload,
            )


# ============================================================
# START REFRESH LOG
# ============================================================

def start_refresh(
    source_id: int,
) -> int:

    sql = text(
        """
        INSERT INTO analytics.data_refresh_runs (
            source_id,
            status
        )
        VALUES (
            :source_id,
            'running'
        )
        RETURNING refresh_id;
        """
    )


    with engine.begin() as connection:

        refresh_id = connection.execute(
            sql,
            {
                "source_id":
                    source_id
            },
        ).scalar_one()


    return int(
        refresh_id
    )


# ============================================================
# FINISH REFRESH LOG
# ============================================================

def finish_refresh(
    refresh_id: int,
    source_id: int,
    status: str,
    schema_changed: bool | None = None,
    rows_read: int = 0,
    rows_inserted: int = 0,
    rows_updated: int = 0,
    rows_unchanged: int = 0,
    rows_rejected: int = 0,
    error_message: str | None = None,
    details: dict | None = None,
):

    details_json = json.dumps(
        details or {}
    )


    refresh_sql = text(
        """
        UPDATE analytics.data_refresh_runs

        SET
            finished_at = NOW(),

            status = :status,

            schema_changed =
                :schema_changed,

            rows_read =
                :rows_read,

            rows_inserted =
                :rows_inserted,

            rows_updated =
                :rows_updated,

            rows_unchanged =
                :rows_unchanged,

            rows_rejected =
                :rows_rejected,

            error_message =
                :error_message,

            details =
                CAST(
                    :details
                    AS jsonb
                )

        WHERE
            refresh_id =
                :refresh_id;
        """
    )


    if status == "success":

        source_sql = text(
            """
            UPDATE analytics.data_sources

            SET
                last_successful_refresh =
                    NOW(),

                last_refresh_status =
                    'success',

                updated_at =
                    NOW()

            WHERE
                source_id =
                    :source_id;
            """
        )

    else:

        source_sql = text(
            """
            UPDATE analytics.data_sources

            SET
                last_refresh_status =
                    'failed',

                updated_at =
                    NOW()

            WHERE
                source_id =
                    :source_id;
            """
        )


    with engine.begin() as connection:

        connection.execute(
            refresh_sql,
            {
                "refresh_id":
                    refresh_id,

                "status":
                    status,

                "schema_changed":
                    schema_changed,

                "rows_read":
                    rows_read,

                "rows_inserted":
                    rows_inserted,

                "rows_updated":
                    rows_updated,

                "rows_unchanged":
                    rows_unchanged,

                "rows_rejected":
                    rows_rejected,

                "error_message":
                    error_message,

                "details":
                    details_json,
            },
        )


        connection.execute(
            source_sql,
            {
                "source_id":
                    source_id
            },
        )


# ============================================================
# REFRESH HISTORY
# ============================================================

def list_refresh_runs(
    source_id: int,
    limit: int = 20,
) -> list[dict]:

    sql = text(
        """
        SELECT *
        FROM analytics.data_refresh_runs

        WHERE
            source_id =
                :source_id

        ORDER BY
            refresh_id DESC

        LIMIT :limit;
        """
    )


    with engine.connect() as connection:

        rows = (
            connection.execute(
                sql,
                {
                    "source_id":
                        source_id,

                    "limit":
                        limit,
                },
            )
            .fetchall()
        )


    return [

        _row_to_dict(
            row
        )

        for row
        in rows
    ]