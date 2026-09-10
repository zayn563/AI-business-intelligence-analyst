from __future__ import annotations

from datetime import date

from sqlalchemy import text

from ..database import engine

from ..dashboard.priority_service import (
    build_business_priorities,
)

from ..data_quality import (
    get_data_freshness_report,
)

from ..intelligence.intelligence_service import (
    latest_complete_periods,
    run_business_intelligence,
)

from ..intelligence.models import (
    IntelligenceRunRequest,
)

from ..intelligence.target_analysis import (
    analyze_targets,
)

from .brief_service import (
    build_business_brief,
)

from .insight_service import (
    get_active_insights,
    sync_business_insights,
)


# ============================================================
# LATEST AVAILABLE SALES DATE
# ============================================================

def get_latest_sales_date() -> date:

    query = text(
        """
        SELECT
            MAX(date_id)
        FROM
            analytics.fact_sales_daily;
        """
    )

    with engine.connect() as connection:

        latest_date = (
            connection.execute(
                query
            )
            .scalar_one()
        )

    if latest_date is None:

        raise ValueError(
            "No sales data is available."
        )

    return latest_date


# ============================================================
# ANALYTICAL PERIOD
# ============================================================

def get_analysis_periods() -> dict:
    """
    Resolve one authoritative analytical cycle.

    The deterministic BI engine already defines the latest
    complete month. Decision intelligence now reuses exactly
    that period instead of independently treating a partial
    latest sales month as the current analytical cycle.
    """

    latest_date = (
        get_latest_sales_date()
    )

    (
        current_period,
        comparison_period,
    ) = (
        latest_complete_periods()
    )

    return {
        "data_through":
            latest_date,

        "current_start":
            current_period.start,

        "current_end":
            current_period.end,

        "comparison_start":
            comparison_period.start,

        "comparison_end":
            comparison_period.end,
    }


# ============================================================
# DECISION INTELLIGENCE RUN
# ============================================================

def run_decision_intelligence() -> dict:

    periods = (
        get_analysis_periods()
    )

    # --------------------------------------------------------
    # 1. Resolve freshness against the SAME completed period
    #    that the decision cycle is about to analyze.
    # --------------------------------------------------------

    freshness = (
        get_data_freshness_report(
            reference_date=
                periods[
                    "current_end"
                ]
        )
    )

    # --------------------------------------------------------
    # 2. Run deterministic business intelligence using the
    #    explicit authoritative periods.
    # --------------------------------------------------------

    intelligence = (
        run_business_intelligence(
            IntelligenceRunRequest(
                current_period={
                    "start":
                        periods[
                            "current_start"
                        ],

                    "end":
                        periods[
                            "current_end"
                        ],
                },

                comparison_period={
                    "start":
                        periods[
                            "comparison_start"
                        ],

                    "end":
                        periods[
                            "comparison_end"
                        ],
                },
            ),
            include_all_material_changes=True,
        )
    )

    # --------------------------------------------------------
    # 3. Run target analysis for the same completed month.
    # --------------------------------------------------------

    target_payload = (
        analyze_targets(
            month_start=
                periods[
                    "current_start"
                ]
        )
    )

    # --------------------------------------------------------
    # 4. Convert signals into management priorities.
    # --------------------------------------------------------

    priorities = (
        build_business_priorities(
            intelligence=
                intelligence,

            target_payload=
                target_payload,

            target_month=
                periods[
                    "current_start"
                ],

            max_risks=
                None,

            max_opportunities=
                None,
        )
    )

    # --------------------------------------------------------
    # 5. Persist / update lifecycle with evidence guardrails.
    # --------------------------------------------------------

    persisted = (
        sync_business_insights(
            priorities=
                priorities,

            period_start=
                periods[
                    "current_start"
                ],

            period_end=
                periods[
                    "current_end"
                ],

            comparison_start=
                periods[
                    "comparison_start"
                ],

            comparison_end=
                periods[
                    "comparison_end"
                ],

            freshness_report=
                freshness,
        )
    )

    # --------------------------------------------------------
    # 6. Read final active state after persistence.
    # --------------------------------------------------------

    active_insights = (
        get_active_insights()
    )

    risks = [
        item
        for item
        in active_insights
        if item.get(
            "type"
        )
        ==
        "risk"
    ]

    opportunities = [
        item
        for item
        in active_insights
        if item.get(
            "type"
        )
        ==
        "opportunity"
    ]

    resolution_blocked = [
        item
        for item
        in active_insights
        if item.get(
            "resolution_blocked"
        )
        is True
    ]

    brief = (
        build_business_brief(
            active_insights
        )
    )

    return {
        "status":
            "completed",

        "data_through":
            periods[
                "data_through"
            ],

        "current_period": {
            "start":
                periods[
                    "current_start"
                ],

            "end":
                periods[
                    "current_end"
                ],
        },

        "comparison_period": {
            "start":
                periods[
                    "comparison_start"
                ],

            "end":
                periods[
                    "comparison_end"
                ],
        },

        "freshness": {
            "status":
                freshness.get(
                    "status"
                ),

            "reference_data_through":
                freshness.get(
                    "reference_data_through"
                ),

            "blocking_datasets":
                freshness.get(
                    "blocking_datasets",
                    [],
                ),

            "mixed_period_warning":
                freshness.get(
                    "mixed_period_warning",
                    False,
                ),
        },

        "targets": {
            "data_available":
                target_payload.get(
                    "data_available",
                    False,
                ),

            "evidence_status":
                target_payload.get(
                    "evidence_status"
                ),

            "regions_evaluated":
                (
                    target_payload.get(
                        "summary",
                        {},
                    )
                    .get(
                        "regions_evaluated",
                        0,
                    )
                ),
        },

        "detected": {
            "risk_count":
                len(
                    priorities.get(
                        "risks",
                        [],
                    )
                ),

            "opportunity_count":
                len(
                    priorities.get(
                        "opportunities",
                        [],
                    )
                ),
        },

        "persisted_count":
            len(
                persisted
            ),

        "active": {
            "risk_count":
                len(
                    risks
                ),

            "opportunity_count":
                len(
                    opportunities
                ),

            "total":
                len(
                    active_insights
                ),

            "resolution_blocked_count":
                len(
                    resolution_blocked
                ),
        },

        "brief":
            brief,
    }