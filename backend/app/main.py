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
# APPLICATION
# ============================================================

app = FastAPI(
    title="AI Business Intelligence Analyst API",
    description=(
        "Deterministic analytics engine with "
        "semantic schema mapping and live data refresh."
    ),
    version="0.3.0",
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
            "0.3.0",

        "status":
            "running",
    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health():

    try:
        db_status = (
            test_database_connection()
        )

        return {
            "api": "healthy",
            "database": db_status,
        }

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error),
        )


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
                    FROM analytics.fact_sales_daily;
                    """
                )
            )
            .fetchone()
        )

        regions = (
            connection.execute(
                text(
                    """
                    SELECT DISTINCT region
                    FROM analytics.dim_store
                    ORDER BY region;
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
                    SELECT DISTINCT category
                    FROM analytics.dim_product
                    ORDER BY category;
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
                    SELECT DISTINCT channel
                    FROM analytics.dim_store
                    ORDER BY channel;
                    """
                )
            )
            .scalars()
            .all()
        )

    return {
        "date_coverage": {
            "start": min_date,
            "end": max_date,
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
            "regions": regions,
            "categories": categories,
            "channels": channels,
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
        return run_sales_analysis(
            request
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error),
        )


# ============================================================
# SEMANTIC SCHEMA
# ============================================================

@app.get("/semantic/schema")
def semantic_schema():

    return canonical_schema_payload()


# ============================================================
# SEMANTIC PROFILE
# ============================================================

@app.post("/semantic/profile")
def semantic_profile(
    request: SemanticMappingRequest,
):

    try:

        return profile_dataset(
            columns=request.columns,
            sample_rows=request.sample_rows,
            max_sample_values=
                request.max_sample_values,
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error),
        )


# ============================================================
# SEMANTIC MAP
# ============================================================

@app.post("/semantic/map")
def semantic_map(
    request: SemanticMappingRequest,
):

    try:

        profile = profile_dataset(
            columns=request.columns,
            sample_rows=request.sample_rows,
            max_sample_values=
                request.max_sample_values,
        )

        mapping = (
            map_profile_to_canonical(
                profile
            )
        )

        return {
            "profile": profile,
            "mapping": mapping,
        }

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error),
        )


# ============================================================
# CREATE DATA SOURCE
# ============================================================

@app.post("/sources")
def create_data_source(
    request: DataSourceCreate,
):

    try:

        return create_source(
            request.model_dump(
                mode="json"
            )
        )

    except Exception as error:

        raise HTTPException(
            status_code=400,
            detail=str(error),
        )


# ============================================================
# LIST DATA SOURCES
# ============================================================

@app.get("/sources")
def get_data_sources():

    return list_sources()


# ============================================================
# GET DATA SOURCE
# ============================================================

@app.get("/sources/{source_id}")
def get_data_source(
    source_id: int,
):

    source = get_source(
        source_id
    )

    if source is None:

        raise HTTPException(
            status_code=404,
            detail="Data source not found.",
        )

    return source


# ============================================================
# UPDATE DATA SOURCE
# ============================================================

@app.patch("/sources/{source_id}")
def update_data_source(
    source_id: int,
    request: DataSourceUpdate,
):

    source = update_source(
        source_id,
        request.model_dump(
            exclude_none=True,
            mode="json",
        ),
    )

    if source is None:

        raise HTTPException(
            status_code=404,
            detail="Data source not found.",
        )

    return source


# ============================================================
# REFRESH DATA SOURCE
# ============================================================

@app.post("/sources/{source_id}/refresh")
def refresh_data_source(
    source_id: int,
):

    try:

        return refresh_source(
            source_id
        )

    except KeyError as error:

        raise HTTPException(
            status_code=404,
            detail=str(error),
        )

    except NotImplementedError as error:

        raise HTTPException(
            status_code=501,
            detail=str(error),
        )

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error),
        )


# ============================================================
# REFRESH HISTORY
# ============================================================

@app.get("/sources/{source_id}/refreshes")
def get_refresh_history(
    source_id: int,
):

    source = get_source(
        source_id
    )

    if source is None:

        raise HTTPException(
            status_code=404,
            detail="Data source not found.",
        )

    return list_refresh_runs(
        source_id
    )