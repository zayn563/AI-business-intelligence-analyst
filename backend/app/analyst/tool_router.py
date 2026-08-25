from datetime import date

from .models import (
    AnalystIntent,
)

from ..intelligence.change_detector import (
    build_change_event,
)

from ..intelligence.driver_analysis import (
    diagnose_change,
)

from ..intelligence.intelligence_service import (
    run_business_intelligence,
)

from ..intelligence.models import (
    IntelligenceRunRequest,
)

from ..intelligence.promotion_analysis import (
    analyze_promotions,
)

from ..intelligence.snapshot_service import (
    get_kpi_snapshot,
    get_max_sales_date,
)

from ..intelligence.target_analysis import (
    analyze_targets,
)


# ============================================================
# ENTITY MATCHING
# ============================================================

def find_entity(
    snapshot: dict,
    requested_value: str,
) -> str | None:

    target = (
        requested_value
        .strip()
        .casefold()
    )

    # Exact match first.
    for key in snapshot:

        if (
            key.casefold()
            ==
            target
        ):

            return key

    # Then partial business-name match.
    for key in snapshot:

        if (
            target
            in
            key.casefold()
        ):

            return key

    return None


# ============================================================
# DIAGNOSTIC TOOL
# ============================================================

def run_diagnostic(
    intent: AnalystIntent,
) -> dict:

    required = [
        intent.metric,
        intent.dimension,
        intent.dimension_value,
        intent.current_start,
        intent.current_end,
        intent.comparison_start,
        intent.comparison_end,
    ]

    if any(
        value is None
        for value
        in required
    ):

        raise ValueError(
            "Diagnostic intent is missing required "
            "metric, dimension, entity or period."
        )

    current_snapshot = (
        get_kpi_snapshot(
            intent.current_start,
            intent.current_end,
            intent.dimension,
        )
    )

    previous_snapshot = (
        get_kpi_snapshot(
            intent.comparison_start,
            intent.comparison_end,
            intent.dimension,
        )
    )

    current_key = (
        find_entity(
            current_snapshot,
            intent.dimension_value,
        )
    )

    previous_key = (
        find_entity(
            previous_snapshot,
            intent.dimension_value,
        )
    )

    if (
        current_key is None
        or
        previous_key is None
    ):

        raise ValueError(
            f"Could not find '{intent.dimension_value}' "
            f"for dimension '{intent.dimension}'."
        )

    current_row = (
        current_snapshot[
            current_key
        ]
    )

    previous_row = (
        previous_snapshot[
            previous_key
        ]
    )

    event = (
        build_change_event(
            metric=
                intent.metric,

            dimension=
                intent.dimension,

            dimension_value=
                current_key,

            current_value=
                current_row.get(
                    intent.metric
                ),

            previous_value=
                previous_row.get(
                    intent.metric
                ),
        )
    )

    if event is None:

        raise ValueError(
            "The requested KPI could not be compared."
        )

    diagnostic = (
        diagnose_change(
            event=
                event,

            current_row=
                current_row,

            previous_row=
                previous_row,
        )
    )

    event[
        "diagnostic"
    ] = diagnostic

    return {
        "tool":
            "diagnose_business_change",

        "data": {
            "current_period": {
                "start":
                    intent.current_start
                    .isoformat(),

                "end":
                    intent.current_end
                    .isoformat(),
            },

            "comparison_period": {
                "start":
                    intent.comparison_start
                    .isoformat(),

                "end":
                    intent.comparison_end
                    .isoformat(),
            },

            "event":
                event,

            "current_snapshot":
                current_row,

            "comparison_snapshot":
                previous_row,
        },
    }


# ============================================================
# TARGET TOOL
# ============================================================

def run_target_tool(
    intent: AnalystIntent,
) -> dict:

    month = (
        intent.target_month
    )

    if month is None:

        latest = (
            get_max_sales_date()
        )

        month = date(
            latest.year,
            latest.month,
            1,
        )

    result = (
        analyze_targets(
            month_start=
                month
        )
    )

    filtered_region = None

    if (
        intent.dimension_value
        is not None
    ):

        target = (
            intent.dimension_value
            .casefold()
        )

        for row in (
            result[
                "region_summary"
            ]
        ):

            if (
                row[
                    "region"
                ]
                .casefold()
                ==
                target
            ):

                filtered_region = row
                break

    return {
        "tool":
            "analyze_targets",

        "data":
            result,

        "focus":
            filtered_region,
    }


# ============================================================
# PROMOTION TOOL
# ============================================================

def run_promotion_tool(
    intent: AnalystIntent,
) -> dict:

    if (
        intent.promotion_start
        is None
        or
        intent.promotion_end
        is None
    ):

        latest = (
            get_max_sales_date()
        )

        start_date = date(
            latest.year,
            1,
            1,
        )

        end_date = (
            latest
        )

    else:

        start_date = (
            intent.promotion_start
        )

        end_date = (
            intent.promotion_end
        )

    result = (
        analyze_promotions(
            start_date=
                start_date,

            end_date=
                end_date,
        )
    )

    return {
        "tool":
            "analyze_promotions",

        "data":
            result,
    }


# ============================================================
# LATEST CHANGES TOOL
# ============================================================

def run_latest_changes_tool() -> dict:

    result = (
        run_business_intelligence(
            IntelligenceRunRequest()
        )
    )

    return {
        "tool":
            "detect_latest_business_changes",

        "data":
            result,
    }


# ============================================================
# ROUTER
# ============================================================

def route_intent(
    intent: AnalystIntent,
) -> dict:

    if (
        intent.analysis_type
        ==
        "diagnostic"
    ):

        return (
            run_diagnostic(
                intent
            )
        )

    if (
        intent.analysis_type
        ==
        "targets"
    ):

        return (
            run_target_tool(
                intent
            )
        )

    if (
        intent.analysis_type
        ==
        "promotions"
    ):

        return (
            run_promotion_tool(
                intent
            )
        )

    if (
        intent.analysis_type
        ==
        "latest_changes"
    ):

        return (
            run_latest_changes_tool()
        )

    return {
        "tool":
            "unsupported",

        "data": {
            "message":
                "The question is outside the currently "
                "supported business intelligence scope."
        },
    }