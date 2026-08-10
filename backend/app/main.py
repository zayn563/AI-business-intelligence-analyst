from fastapi import (
    FastAPI,
    HTTPException,
)

from sqlalchemy import text

from .database import (
    engine,
    test_database_connection,
)

from .metrics import (
    SALES_DIMENSIONS,
    SALES_METRICS,
)

from .schemas import (
    AnalysisRequest,
    DataSourceCreate,
    DataSourceUpdate,
    SemanticMappingRequest,
)

from .services.orchestration_service import (
    get_pipeline_status,
    refresh_active_sources,
)

from .services.refresh_service import (
    refresh_source,
)

from .services.sales_service import (
    run_sales_analysis,
)

from .semantic.canonical_schema import (
    canonical_schema_payload,
)

from .semantic.mapper import (
    map_profile_to_canonical,
)

from .semantic.profiler import (
    profile_dataset,
)

from .sources.registry import (
    create_source,
    get_source,
    list_refresh_runs,
    list_sources,
    update_source,
)


# ============================================================
# ERROR DETAIL
# ============================================================

def error_detail(
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
# APPLICATION
# ============================================================

app = FastAPI(
    title=(
        "AI Business Intelligence "
        "Analyst API"
    ),
    description=(
        "Deterministic analytics, "
        "semantic source mapping, "
        "live data refresh and "
        "business intelligence services."
    ),
    version="0.4.0",
)


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():

    return {
        "application":
            "AI Business Intelligence Analyst",

        "version":
            "0.4.0",

        "status":
            "running",
    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health():

    try:

        database = (
            test_database_connection()
        )

        return {
            "api":
                "healthy",

            "database":
                database,
        }

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=error_detail(
                error
            ),
        ) from error


# ============================================================
# PIPELINE STATUS
#
# This is intended for:
# - frontend
# - monitoring
# - n8n
# ============================================================

@app.get("/pipeline/status")
def pipeline_status():

    try:

        return (
            get_pipeline_status()
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=error_detail(
                error
            ),
        ) from error


# ============================================================
# REFRESH ALL ACTIVE SOURCES
#
# n8n will call THIS endpoint.
#
# It intentionally does not contain
# a hard-coded source ID.
# ============================================================

@app.post("/pipeline/refresh")
def pipeline_refresh():

    try:

        return (
            refresh_active_sources()
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=error_detail(
                error
            ),
        ) from error


# ============================================================
# ANALYTICS METADATA
# ============================================================

@app.get("/metadata")
def metadata():

    with engine.connect() as connection:

        min_date, max_date = (
            connection.execute(
                text(
                    """
                    SELECT
                        MIN(date_id),
                        MAX(date_id)
                    FROM
                        analytics.fact_sales_daily;
                    """
                )
            )
            .fetchone()
        )

        regions = (
            connection.execute(
                text(
                    """
                    SELECT DISTINCT
                        region
                    FROM
                        analytics.dim_store
                    ORDER BY
                        region;
                    """
                )
            )
            .scalars()
            .all()
        )

        categories = (
            connection.execute(
                text(
                    """
                    SELECT DISTINCT
                        category
                    FROM
                        analytics.dim_product
                    ORDER BY
                        category;
                    """
                )
            )
            .scalars()
            .all()
        )

        channels = (
            connection.execute(
                text(
                    """
                    SELECT DISTINCT
                        channel
                    FROM
                        analytics.dim_store
                    ORDER BY
                        channel;
                    """
                )
            )
            .scalars()
            .all()
        )

    return {
        "date_coverage": {
            "start":
                min_date,

            "end":
                max_date,
        },

        "supported_metrics":
            list(
                SALES_METRICS.keys()
            ),

        "supported_dimensions":
            list(
                SALES_DIMENSIONS.keys()
            ),

        "available_values": {
            "regions":
                regions,

            "categories":
                categories,

            "channels":
                channels,
        },
    }


# ============================================================
# ANALYSIS
# ============================================================

@app.post("/analyze")
def analyze(
    request: AnalysisRequest,
):

    try:

        return (
            run_sales_analysis(
                request
            )
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=error_detail(
                error
            ),
        ) from error


# ============================================================
# SEMANTIC SCHEMA
# ============================================================

@app.get("/semantic/schema")
def semantic_schema():

    return (
        canonical_schema_payload()
    )


# ============================================================
# SEMANTIC PROFILE
# ============================================================

@app.post("/semantic/profile")
def semantic_profile(
    request: SemanticMappingRequest,
):

    try:

        return (
            profile_dataset(
                columns=
                    request.columns,

                sample_rows=
                    request.sample_rows,

                max_sample_values=
                    request.max_sample_values,
            )
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=error_detail(
                error
            ),
        ) from error


# ============================================================
# SEMANTIC MAP
# ============================================================

@app.post("/semantic/map")
def semantic_map(
    request: SemanticMappingRequest,
):

    try:

        profile = (
            profile_dataset(
                columns=
                    request.columns,

                sample_rows=
                    request.sample_rows,

                max_sample_values=
                    request.max_sample_values,
            )
        )

        mapping = (
            map_profile_to_canonical(
                profile
            )
        )

        return {
            "profile":
                profile,

            "mapping":
                mapping,
        }

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=error_detail(
                error
            ),
        ) from error


# ============================================================
# CREATE SOURCE
# ============================================================

@app.post("/sources")
def create_data_source(
    request: DataSourceCreate,
):

    try:

        return (
            create_source(
                request.model_dump(
                    mode="json"
                )
            )
        )

    except Exception as error:

        raise HTTPException(
            status_code=400,
            detail=error_detail(
                error
            ),
        ) from error


# ============================================================
# LIST SOURCES
# ============================================================

@app.get("/sources")
def get_data_sources():

    return (
        list_sources()
    )


# ============================================================
# GET SOURCE
# ============================================================

@app.get("/sources/{source_id}")
def get_data_source(
    source_id: int,
):

    source = (
        get_source(
            source_id
        )
    )

    if source is None:

        raise HTTPException(
            status_code=404,
            detail=(
                "Data source not found."
            ),
        )

    return source


# ============================================================
# UPDATE SOURCE
# ============================================================

@app.patch("/sources/{source_id}")
def update_data_source(
    source_id: int,
    request: DataSourceUpdate,
):

    source = (
        update_source(
            source_id,

            request.model_dump(
                exclude_none=True,
                mode="json",
            ),
        )
    )

    if source is None:

        raise HTTPException(
            status_code=404,
            detail=(
                "Data source not found."
            ),
        )

    return source


# ============================================================
# REFRESH ONE SOURCE
#
# Kept for debugging/admin operations.
# n8n should use /pipeline/refresh instead.
# ============================================================

@app.post("/sources/{source_id}/refresh")
def refresh_data_source(
    source_id: int,
):

    try:

        return (
            refresh_source(
                source_id
            )
        )

    except KeyError as error:

        raise HTTPException(
            status_code=404,
            detail=error_detail(
                error
            ),
        ) from error

    except NotImplementedError as error:

        raise HTTPException(
            status_code=501,
            detail=error_detail(
                error
            ),
        ) from error

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=error_detail(
                error
            ),
        ) from error

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=error_detail(
                error
            ),
        ) from error


# ============================================================
# REFRESH HISTORY
# ============================================================

@app.get("/sources/{source_id}/refreshes")
def get_refresh_history(
    source_id: int,
):

    source = (
        get_source(
            source_id
        )
    )

    if source is None:

        raise HTTPException(
            status_code=404,
            detail=(
                "Data source not found."
            ),
        )

    return (
        list_refresh_runs(
            source_id
        )
    )