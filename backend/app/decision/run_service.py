from __future__ import annotations

from datetime import (
    date,
    timedelta,
)

from sqlalchemy import text

from ..database import engine

from ..dashboard.priority_service import (
    build_business_priorities,
)

from ..intelligence.intelligence_service import (
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

    latest_date = (
        get_latest_sales_date()
    )

    current_start = date(
        latest_date.year,
        latest_date.month,
        1,
    )

    current_end = (
        latest_date
    )

    comparison_end = (
        current_start
        -
        timedelta(
            days=1
        )
    )

    comparison_start = date(
        comparison_end.year,
        comparison_end.month,
        1,
    )

    return {
        "data_through":
            latest_date,

        "current_start":
            current_start,

        "current_end":
            current_end,

        "comparison_start":
            comparison_start,

        "comparison_end":
            comparison_end,
    }


# ============================================================
# DECISION INTELLIGENCE RUN
# ============================================================

def run_decision_intelligence() -> dict:

    periods = (
        get_analysis_periods()
    )

    # --------------------------------------------------------
    # 1. Run deterministic business-intelligence engine.
    # --------------------------------------------------------

    intelligence = (
        run_business_intelligence(
            IntelligenceRunRequest()
        )
    )

    # --------------------------------------------------------
    # 2. Run deterministic target analysis.
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
    # 3. Convert individual signals into management priorities.
    #
    # We deliberately ask for a large result set here because
    # persistence should not be limited to the three cards shown
    # on the dashboard.
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
                100,

            max_opportunities=
                100,
        )
    )

    # --------------------------------------------------------
    # 4. Persist / update lifecycle.
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
        )
    )

    # --------------------------------------------------------
    # 5. Read the final active state back from persistence.
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
        },

        "brief":
            brief,
    }