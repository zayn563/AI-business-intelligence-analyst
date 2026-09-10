from __future__ import annotations

from copy import deepcopy

from typing import Any


# ============================================================
# PROFITABILITY METRIC FAMILY
# ============================================================

PROFITABILITY_METRICS = {
    "gross_profit",
    "margin_pct",
    "discount_pct",
    "cost_per_unit",
}


# ============================================================
# BASIC HELPERS
# ============================================================

def _normalize_text(
    value: Any,
) -> str:

    if value is None:
        return ""

    return (
        str(value)
        .strip()
        .lower()
    )


def _profitability_policy() -> dict:

    return {
        "management_focus":
            (
                "Protect profitability by isolating the "
                "commercial sources of margin and profit "
                "pressure."
            ),

        "recommended_actions": [
            (
                "Identify products, stores and channels "
                "with the largest contribution to profit "
                "or margin deterioration."
            ),
            (
                "Review discount intensity, selling price "
                "and cost pressure before taking broad "
                "pricing action."
            ),
            (
                "Use Scenario Lab to test commercially "
                "realistic recovery options and track "
                "gross profit and margin after execution."
            ),
        ],

        "expected_kpis": [
            "gross_profit",
            "margin_pct",
            "discount_pct",
            "avg_selling_price",
            "cost_per_unit",
        ],

        "action_type":
            "profitability",
    }


# ============================================================
# RECOMMENDATION MATCHING
# ============================================================

def _is_profitability_recommendation(
    recommendation: dict,
) -> bool:

    metric = (
        _normalize_text(
            recommendation.get(
                "primary_metric"
            )
        )
    )

    title = (
        _normalize_text(
            recommendation.get(
                "title"
            )
        )
    )

    return (
        metric
        in PROFITABILITY_METRICS
        or
        "margin"
        in title
        or
        "profit"
        in title
    )


# ============================================================
# ANSWER COMPOSER
# ============================================================

def _compose_profitability_answer(
    recommendations: list[dict],
    requested_region: str | None,
) -> str:

    if not recommendations:

        return (
            "There are currently no active persisted "
            "profitability priorities matching this request."
        )

    if requested_region:

        opening = (
            f"{requested_region} currently has "
            f"{len(recommendations)} profitability-relevant "
            "priority signal"
        )

        if (
            len(recommendations)
            !=
            1
        ):

            opening += "s"

        opening += "."

    else:

        opening = (
            "The current priority layer contains the following "
            "profitability-relevant priorities."
        )

    sections = [
        opening
    ]

    for (
        index,
        recommendation,
    ) in enumerate(
        recommendations,
        start=1,
    ):

        scope = (
            recommendation.get(
                "dimension_value"
            )
            or
            recommendation.get(
                "dimension"
            )
            or
            "Business"
        )

        severity = (
            str(
                recommendation.get(
                    "severity"
                )
                or
                "unknown"
            )
            .lower()
        )

        score = (
            recommendation.get(
                "priority_score"
            )
        )

        score_text = (
            f", score {score:.1f}"
            if isinstance(
                score,
                (
                    int,
                    float,
                ),
            )
            else
            ""
        )

        management_focus = (
            str(
                recommendation.get(
                    "management_focus"
                )
                or
                "Investigate the profitability signal."
            )
        )

        evidence_items = (
            recommendation.get(
                "evidence"
            )
            or
            []
        )

        first_evidence = (
            evidence_items[0]
            if (
                isinstance(
                    evidence_items,
                    list,
                )
                and
                evidence_items
            )
            else
            (
                "This priority is present in the "
                "persisted intelligence layer."
            )
        )

        actions = (
            recommendation.get(
                "recommended_actions"
            )
            or
            []
        )

        first_action = (
            actions[0]
            if (
                isinstance(
                    actions,
                    list,
                )
                and
                actions
            )
            else
            management_focus
        )

        sections.append(
            (
                f"{index}. {scope} "
                f"({severity}{score_text}): "
                f"{management_focus} "
                f"Evidence: {first_evidence}. "
                f"Recommended action: {first_action}"
            )
        )

    return (
        "\n\n".join(
            sections
        )
    )


# ============================================================
# PUBLIC FOCUS GUARD
# ============================================================

def apply_recommendation_focus_guard(
    result: dict,
) -> dict:
    """
    Keep deterministic recommendations aligned with an explicit
    user business focus.

    Why this is needed:

    A persisted insight can legitimately transition from risk to
    opportunity after a new data period. If the user explicitly
    asks about margin or profitability deterioration, the latest
    insight may still be an opportunity while its primary metric
    remains gross_profit or margin_pct.

    The recommendation engine's generic opportunity-first policy
    can therefore return action_type='growth'. This guard preserves
    the underlying evidence and KPI values while making the action
    policy consistent with the user's explicit profitability focus.
    """

    guarded = (
        deepcopy(
            result
        )
    )

    evidence = (
        guarded.get(
            "evidence"
        )
    )

    if not isinstance(
        evidence,
        dict,
    ):

        return guarded

    question_focus = (
        _normalize_text(
            evidence.get(
                "question_focus"
            )
        )
    )

    if (
        question_focus
        !=
        "profitability"
    ):

        return guarded

    recommendations = (
        evidence.get(
            "recommendations"
        )
    )

    if not isinstance(
        recommendations,
        list,
    ):

        return guarded

    policy = (
        _profitability_policy()
    )

    changed = False

    for recommendation in recommendations:

        if not isinstance(
            recommendation,
            dict,
        ):

            continue

        if not (
            _is_profitability_recommendation(
                recommendation
            )
        ):

            continue

        recommendation[
            "management_focus"
        ] = (
            policy[
                "management_focus"
            ]
        )

        recommendation[
            "recommended_actions"
        ] = list(
            policy[
                "recommended_actions"
            ]
        )

        recommendation[
            "expected_kpis"
        ] = list(
            policy[
                "expected_kpis"
            ]
        )

        recommendation[
            "action_type"
        ] = (
            policy[
                "action_type"
            ]
        )

        action_template = (
            recommendation.get(
                "action_template"
            )
        )

        if isinstance(
            action_template,
            dict,
        ):

            action_scope = (
                recommendation.get(
                    "dimension_value"
                )
                or
                recommendation.get(
                    "dimension"
                )
                or
                "Business"
            )

            action_template[
                "title"
            ] = (
                f"{action_scope}: "
                f"{policy['management_focus']}"
            )

        changed = True

    if changed:

        guarded[
            "answer"
        ] = (
            _compose_profitability_answer(
                recommendations,
                evidence.get(
                    "requested_region"
                ),
            )
        )

    return guarded