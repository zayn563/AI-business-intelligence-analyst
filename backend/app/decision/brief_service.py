from __future__ import annotations


# ============================================================
# MORNING BRIEF
# ============================================================

def build_business_brief(
    active_insights: list[dict],
) -> dict:

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


    if risks:

        headline = (
            f"{len(risks)} business issue"
            f"{'' if len(risks) == 1 else 's'} "
            "require attention."
        )


        top = (
            risks[
                0
            ]
        )


        focus = {

            "title":
                top[
                    "title"
                ],

            "reason":
                (
                    f"{top['primary_metric'].replace('_', ' ').title()} "
                    f"changed {top['primary_change']}."
                ),

            "recommended_action":
                top.get(
                    "recommended_action"
                ),

            "insight_id":
                top.get(
                    "insight_id"
                ),
        }


    else:

        headline = (
            "No active high-priority risks were detected."
        )


        focus = None


    return {

        "headline":
            headline,

        "risk_count":
            len(
                risks
            ),

        "opportunity_count":
            len(
                opportunities
            ),

        "recommended_focus":
            focus,

        "key_risks": [
            {
                "insight_id":
                    item.get(
                        "insight_id"
                    ),

                "title":
                    item[
                        "title"
                    ],

                "change":
                    item[
                        "primary_change"
                    ],

                "status":
                    item.get(
                        "lifecycle_status"
                    ),
            }
            for item
            in risks[
                :3
            ]
        ],

        "key_opportunities": [
            {
                "insight_id":
                    item.get(
                        "insight_id"
                    ),

                "title":
                    item[
                        "title"
                    ],

                "change":
                    item[
                        "primary_change"
                    ],
            }
            for item
            in opportunities[
                :2
            ]
        ],
    }