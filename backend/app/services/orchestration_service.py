from datetime import (
    datetime,
    timezone,
)

from .refresh_service import (
    refresh_source,
)

from ..sources.registry import (
    list_sources,
)


# ============================================================
# UTC TIMESTAMP
# ============================================================

def utc_now_iso() -> str:

    return (
        datetime
        .now(
            timezone.utc
        )
        .isoformat()
    )


# ============================================================
# FRIENDLY ERROR
# ============================================================

def error_text(
    error: Exception,
) -> str:

    message = str(
        error
    ).strip()

    if not message:

        message = repr(
            error
        )

    return (
        f"{type(error).__name__}: "
        f"{message}"
    )


# ============================================================
# PIPELINE STATUS
# ============================================================

def get_pipeline_status() -> dict:

    sources = (
        list_sources()
    )

    active_sources = [
        source
        for source
        in sources
        if source.get(
            "is_active"
        )
    ]

    healthy_sources = [
        source
        for source
        in active_sources
        if source.get(
            "last_refresh_status"
        )
        ==
        "success"
    ]

    unhealthy_sources = [
        source
        for source
        in active_sources
        if source.get(
            "last_refresh_status"
        )
        not in {
            None,
            "success",
        }
    ]

    pending_sources = [
        source
        for source
        in active_sources
        if source.get(
            "last_refresh_status"
        )
        is None
    ]

    if not active_sources:

        overall_status = (
            "no_active_sources"
        )

    elif len(
        healthy_sources
    ) == len(
        active_sources
    ):

        overall_status = (
            "healthy"
        )

    elif unhealthy_sources:

        overall_status = (
            "attention_required"
        )

    else:

        overall_status = (
            "pending"
        )

    return {
        "status":
            overall_status,

        "checked_at":
            utc_now_iso(),

        "sources_total":
            len(
                sources
            ),

        "active_sources":
            len(
                active_sources
            ),

        "healthy_sources":
            len(
                healthy_sources
            ),

        "pending_sources":
            len(
                pending_sources
            ),

        "unhealthy_sources":
            len(
                unhealthy_sources
            ),

        "sources":
            active_sources,
    }


# ============================================================
# REFRESH ALL ACTIVE SOURCES
# ============================================================

def refresh_active_sources() -> dict:

    started_at = (
        utc_now_iso()
    )

    sources = (
        list_sources()
    )

    active_sources = [
        source
        for source
        in sources
        if source.get(
            "is_active"
        )
    ]

    # --------------------------------------------------------
    # Nothing to refresh
    # --------------------------------------------------------

    if not active_sources:

        return {
            "status":
                "no_active_sources",

            "started_at":
                started_at,

            "finished_at":
                utc_now_iso(),

            "sources_attempted":
                0,

            "sources_succeeded":
                0,

            "sources_failed":
                0,

            "rows_read":
                0,

            "rows_inserted":
                0,

            "rows_updated":
                0,

            "rows_unchanged":
                0,

            "rows_rejected":
                0,

            "results":
                [],
        }

    # --------------------------------------------------------
    # Execute each source independently
    # --------------------------------------------------------

    results = []

    for source in active_sources:

        source_id = source[
            "source_id"
        ]

        try:

            result = (
                refresh_source(
                    source_id
                )
            )

            results.append(
                {
                    **result,
                    "pipeline_status":
                        "success",
                }
            )

        except Exception as error:

            results.append(
                {
                    "source_id":
                        source_id,

                    "source_name":
                        source.get(
                            "source_name"
                        ),

                    "source_type":
                        source.get(
                            "source_type"
                        ),

                    "pipeline_status":
                        "failed",

                    "error":
                        error_text(
                            error
                        ),

                    "rows_read":
                        0,

                    "rows_inserted":
                        0,

                    "rows_updated":
                        0,

                    "rows_unchanged":
                        0,

                    "rows_rejected":
                        0,
                }
            )

    # --------------------------------------------------------
    # Aggregate
    # --------------------------------------------------------

    succeeded = [
        result
        for result
        in results
        if result.get(
            "pipeline_status"
        )
        ==
        "success"
    ]

    failed = [
        result
        for result
        in results
        if result.get(
            "pipeline_status"
        )
        ==
        "failed"
    ]

    if len(
        succeeded
    ) == len(
        results
    ):

        overall_status = (
            "success"
        )

    elif succeeded:

        overall_status = (
            "partial_success"
        )

    else:

        overall_status = (
            "failed"
        )

    def total(
        field: str,
    ) -> int:

        return sum(
            int(
                result.get(
                    field,
                    0,
                )
                or 0
            )
            for result
            in results
        )

    return {
        "status":
            overall_status,

        "started_at":
            started_at,

        "finished_at":
            utc_now_iso(),

        "sources_attempted":
            len(
                results
            ),

        "sources_succeeded":
            len(
                succeeded
            ),

        "sources_failed":
            len(
                failed
            ),

        "rows_read":
            total(
                "rows_read"
            ),

        "rows_inserted":
            total(
                "rows_inserted"
            ),

        "rows_updated":
            total(
                "rows_updated"
            ),

        "rows_unchanged":
            total(
                "rows_unchanged"
            ),

        "rows_rejected":
            total(
                "rows_rejected"
            ),

        "results":
            results,
    }