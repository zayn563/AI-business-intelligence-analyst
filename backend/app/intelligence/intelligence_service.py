from calendar import monthrange
from collections import Counter
from datetime import (
    date,
    timedelta,
)

from .change_detector import (
    compare_snapshots,
)

from .driver_analysis import (
    diagnose_change,
)

from .models import (
    IntelligenceRunRequest,
    PeriodRange,
)

from .snapshot_service import (
    get_kpi_snapshot,
    get_max_sales_date,
)

from .thresholds import (
    SEVERITY_RANK,
)


# ============================================================
# PERIOD RESOLUTION
# ============================================================

def latest_complete_periods() -> tuple[
    PeriodRange,
    PeriodRange,
]:

    max_date = (
        get_max_sales_date()
    )

    last_day = (
        monthrange(
            max_date.year,
            max_date.month,
        )[1]
    )

    # Data reaches month-end:
    # use that month.
    if (
        max_date.day
        ==
        last_day
    ):

        current_end = (
            max_date
        )

        current_start = (
            date(
                max_date.year,
                max_date.month,
                1,
            )
        )

    # Incomplete latest month:
    # use previous complete month.
    else:

        current_end = (
            date(
                max_date.year,
                max_date.month,
                1,
            )
            -
            timedelta(
                days=1
            )
        )

        current_start = (
            date(
                current_end.year,
                current_end.month,
                1,
            )
        )

    comparison_end = (
        current_start
        -
        timedelta(
            days=1
        )
    )

    comparison_start = (
        date(
            comparison_end.year,
            comparison_end.month,
            1,
        )
    )

    return (
        PeriodRange(
            start=current_start,
            end=current_end,
        ),
        PeriodRange(
            start=comparison_start,
            end=comparison_end,
        ),
    )


def resolve_periods(
    request: IntelligenceRunRequest,
) -> tuple[
    PeriodRange,
    PeriodRange,
]:

    if (
        request.current_period
        is not None
    ):

        return (
            request.current_period,
            request.comparison_period,
        )

    return (
        latest_complete_periods()
    )


# ============================================================
# SORTING
# ============================================================

def event_magnitude(
    event: dict,
) -> float:

    if (
        event.get(
            "change_pp"
        )
        is not None
    ):

        return abs(
            event[
                "change_pp"
            ]
        )

    if (
        event.get(
            "change_pct"
        )
        is not None
    ):

        return abs(
            event[
                "change_pct"
            ]
        )

    return 0.0


def event_sort_key(
    event: dict,
):

    return (
        SEVERITY_RANK.get(
            event[
                "severity"
            ],
            0,
        ),
        event_magnitude(
            event
        ),
    )


# ============================================================
# MAIN INTELLIGENCE ENGINE
# ============================================================

def run_business_intelligence(
    request: IntelligenceRunRequest,
) -> dict:

    (
        current_period,
        comparison_period,
    ) = resolve_periods(
        request
    )

    # ========================================================
    # OVERALL BUSINESS VIEW
    # ========================================================

    current_overall = (
        get_kpi_snapshot(
            current_period.start,
            current_period.end,
            "overall",
        )
    )

    previous_overall = (
        get_kpi_snapshot(
            comparison_period.start,
            comparison_period.end,
            "overall",
        )
    )

    overview = (
        compare_snapshots(
            current_snapshot=
                current_overall,

            previous_snapshot=
                previous_overall,

            dimension=
                "overall",

            metrics=
                request.metrics,
        )
    )


    # ========================================================
    # DIMENSION-LEVEL DETECTION
    # ========================================================

    all_events = []

    dimension_summary = {}

    for dimension in (
        request.dimensions
    ):

        if (
            dimension
            ==
            "overall"
        ):

            continue

        current_snapshot = (
            get_kpi_snapshot(
                current_period.start,
                current_period.end,
                dimension,
            )
        )

        previous_snapshot = (
            get_kpi_snapshot(
                comparison_period.start,
                comparison_period.end,
                dimension,
            )
        )

        events = (
            compare_snapshots(
                current_snapshot=
                    current_snapshot,

                previous_snapshot=
                    previous_snapshot,

                dimension=
                    dimension,

                metrics=
                    request.metrics,
            )
        )

        material_events = []

        for event in events:

            if (
                not event[
                    "material"
                ]
            ):

                continue

            entity = (
                event[
                    "dimension_value"
                ]
            )

            current_row = (
                current_snapshot[
                    entity
                ]
            )

            previous_row = (
                previous_snapshot[
                    entity
                ]
            )

            event[
                "diagnostic"
            ] = (
                diagnose_change(
                    event=
                        event,

                    current_row=
                        current_row,

                    previous_row=
                        previous_row,
                )
            )

            material_events.append(
                event
            )

        dimension_summary[
            dimension
        ] = {
            "entities_compared":
                len(
                    set(
                        current_snapshot.keys()
                    )
                    &
                    set(
                        previous_snapshot.keys()
                    )
                ),

            "material_changes":
                len(
                    material_events
                ),
        }

        all_events.extend(
            material_events
        )


    # ========================================================
    # RANK ALERTS
    # ========================================================

    all_events.sort(
        key=
            event_sort_key,
        reverse=True,
    )

    top_changes = (
        all_events[
            :request.top_n
        ]
    )


    # ========================================================
    # SUMMARY COUNTS
    # ========================================================

    severity_counts = (
        Counter(
            event[
                "severity"
            ]
            for event
            in all_events
        )
    )

    negative_changes = sum(
        1
        for event
        in all_events
        if event[
            "impact"
        ]
        ==
        "negative"
    )

    positive_changes = sum(
        1
        for event
        in all_events
        if event[
            "impact"
        ]
        ==
        "positive"
    )


    # ========================================================
    # RESPONSE
    # ========================================================

    return {
        "status":
            "success",

        "analysis_type":
            "business_change_detection",

        "data_as_of":
            get_max_sales_date()
            .isoformat(),

        "current_period": {
            "start":
                current_period.start
                .isoformat(),

            "end":
                current_period.end
                .isoformat(),
        },

        "comparison_period": {
            "start":
                comparison_period.start
                .isoformat(),

            "end":
                comparison_period.end
                .isoformat(),
        },

        "overview":
            overview,

        "alert_summary": {
            "total_material_changes":
                len(
                    all_events
                ),

            "high":
                severity_counts.get(
                    "high",
                    0,
                ),

            "medium":
                severity_counts.get(
                    "medium",
                    0,
                ),

            "low":
                severity_counts.get(
                    "low",
                    0,
                ),

            "negative":
                negative_changes,

            "positive":
                positive_changes,
        },

        "dimension_summary":
            dimension_summary,

        "top_changes":
            top_changes,
    }