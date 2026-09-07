from __future__ import annotations


# ============================================================
# HELPERS
# ============================================================

def is_resolution_blocked(
    insight: dict,
) -> bool:

    return (
        insight.get(
            "resolution_blocked"
        )
        is True
    )


def dataset_label(
    value: object,
) -> str:

    text = (
        str(
            value
        )
        .strip()
        .replace(
            "_",
            " ",
        )
    )

    if not text:

        return "Evidence"

    return text.title()


def blocker_text(
    insight: dict,
) -> str:

    blockers = (
        insight.get(
            "blocking_datasets"
        )
        or
        []
    )

    labels = [
        dataset_label(
            blocker
        )
        for blocker
        in blockers
    ]

    if not labels:

        return "required evidence"

    return ", ".join(
        labels
    )


# ============================================================
# MORNING / MANAGEMENT BRIEF
# ============================================================

def build_business_brief(
    active_insights: list[dict],
) -> dict:

    all_risks = [
        item
        for item
        in active_insights
        if item.get(
            "type"
        )
        ==
        "risk"
    ]

    all_opportunities = [
        item
        for item
        in active_insights
        if item.get(
            "type"
        )
        ==
        "opportunity"
    ]

    current_risks = [
        item
        for item
        in all_risks
        if not is_resolution_blocked(
            item
        )
    ]

    blocked_risks = [
        item
        for item
        in all_risks
        if is_resolution_blocked(
            item
        )
    ]

    current_opportunities = [
        item
        for item
        in all_opportunities
        if not is_resolution_blocked(
            item
        )
    ]

    blocked_opportunities = [
        item
        for item
        in all_opportunities
        if is_resolution_blocked(
            item
        )
    ]

    # ========================================================
    # HEADLINE
    # ========================================================

    if (
        current_risks
        and
        blocked_risks
    ):

        headline = (
            f"{len(current_risks)} current business "
            f"{'risk' if len(current_risks) == 1 else 'risks'} "
            "require attention; "
            f"{len(blocked_risks)} prior "
            f"{'issue remains' if len(blocked_risks) == 1 else 'issues remain'} "
            "open pending current evidence."
        )

    elif current_risks:

        headline = (
            f"{len(current_risks)} current business "
            f"{'risk requires' if len(current_risks) == 1 else 'risks require'} "
            "management attention."
        )

    elif blocked_risks:

        headline = (
            "No current-period risk requires action, but "
            f"{len(blocked_risks)} prior "
            f"{'issue remains' if len(blocked_risks) == 1 else 'issues remain'} "
            "open because required evidence is not current."
        )

    else:

        headline = (
            "No active business risks currently require "
            "management attention."
        )

    # ========================================================
    # MANAGEMENT FOCUS
    # ========================================================

    focus_source = (
        current_risks[
            0
        ]
        if current_risks
        else
        (
            blocked_risks[
                0
            ]
            if blocked_risks
            else
            None
        )
    )

    if focus_source is None:

        focus = None

    else:

        blocked = (
            is_resolution_blocked(
                focus_source
            )
        )

        if blocked:

            blockers = (
                blocker_text(
                    focus_source
                )
            )

            action_text = (
                f"Refresh {blockers} and rerun decision intelligence "
                "before treating this issue as resolved or changing "
                "the management response."
            )

            reason = (
                "The issue remains open because its required "
                f"evidence is not current: {blockers}."
            )

        else:

            action_text = (
                focus_source.get(
                    "recommended_action"
                )
            )

            reason = (
                f"{str(focus_source.get('primary_metric') or 'Performance').replace('_', ' ').title()} "
                f"changed {focus_source.get('primary_change') or 'materially'}."
            )

        focus = {

            "title":
                focus_source[
                    "title"
                ],

            "reason":
                reason,

            "recommended_action":
                action_text,

            "insight_id":
                focus_source.get(
                    "insight_id"
                ),

            "evidence_status":
                focus_source.get(
                    "evidence_status"
                ),

            "resolution_blocked":
                blocked,

            "blocking_datasets":
                list(
                    focus_source.get(
                        "blocking_datasets"
                    )
                    or
                    []
                ),
        }

    # ========================================================
    # RETURN
    # ========================================================

    return {

        # Current actionable counts.
        "risk_count":
            len(
                current_risks
            ),

        "current_risk_count":
            len(
                current_risks
            ),

        "opportunity_count":
            len(
                current_opportunities
            ),

        "current_opportunity_count":
            len(
                current_opportunities
            ),

        # Total persisted active counts.
        "active_risk_count":
            len(
                all_risks
            ),

        "active_opportunity_count":
            len(
                all_opportunities
            ),

        # Evidence-held counts.
        "evidence_blocked_risk_count":
            len(
                blocked_risks
            ),

        "evidence_blocked_opportunity_count":
            len(
                blocked_opportunities
            ),

        "headline":
            headline,

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

                "resolution_blocked":
                    is_resolution_blocked(
                        item
                    ),
            }
            for item
            in (
                current_risks
                +
                blocked_risks
            )[
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

                "resolution_blocked":
                    is_resolution_blocked(
                        item
                    ),
            }
            for item
            in (
                current_opportunities
                +
                blocked_opportunities
            )[
                :2
            ]
        ],
    }