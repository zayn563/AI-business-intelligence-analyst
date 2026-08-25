import json

from ..config import settings

from .llm_client import (
    clean_llm_text,
    get_llm_client,
    get_ollama_model,
    llm_available,
)

from .models import (
    AnalystIntent,
)


# ============================================================
# METRIC LABELS
# ============================================================

METRIC_LABELS = {
    "net_sales":
        "net sales",

    "units_sold":
        "units",

    "transactions":
        "transactions",

    "gross_profit":
        "gross profit",

    "margin_pct":
        "gross margin",

    "avg_selling_price":
        "average selling price",

    "discount_pct":
        "discount rate",

    "cost_per_unit":
        "cost per unit",

    "stockout_rate":
        "stockout rate",
}


# ============================================================
# DIAGNOSIS LABELS
# ============================================================

DIAGNOSIS_LABELS = {
    "volume_and_availability":
        "volume decline with availability pressure",

    "volume_decline":
        "volume decline",

    "price_decline":
        "pricing pressure",

    "promotion_led_growth":
        "promotion-led growth",

    "promotion_led_volume_growth":
        "promotion-led volume growth",

    "price_led_growth":
        "price-led growth",

    "volume_led_growth":
        "volume-led growth",

    "discount_and_cost_pressure":
        "combined discount and cost pressure",

    "cost_pressure":
        "cost pressure",

    "discount_pressure":
        "discount pressure",

    "availability_deterioration":
        "availability deterioration",

    "availability_improvement":
        "availability improvement",

    "availability_related_volume_pressure":
        "availability-related volume pressure",

    "pricing_change":
        "pricing change",

    "promotional_intensity_change":
        "change in promotional intensity",

    "mixed_or_unexplained":
        "mixed or currently unexplained drivers",
}


# ============================================================
# GENERAL HELPERS
# ============================================================

def safe_float(
    value,
) -> float | None:

    if value is None:

        return None

    try:

        return float(
            value
        )

    except (
        TypeError,
        ValueError,
    ):

        return None


def format_change(
    event: dict,
) -> str:

    change_pp = (
        safe_float(
            event.get(
                "change_pp"
            )
        )
    )

    if change_pp is not None:

        return (
            f"{abs(change_pp):.2f} "
            "percentage points"
        )

    change_pct = (
        safe_float(
            event.get(
                "change_pct"
            )
        )
    )

    if change_pct is not None:

        return (
            f"{abs(change_pct):.2f}%"
        )

    return (
        "an unavailable amount"
    )


def format_pct_driver(
    label: str,
    value,
) -> str | None:

    numeric_value = (
        safe_float(
            value
        )
    )

    if numeric_value is None:

        return None

    if numeric_value > 0:

        direction = (
            "increased"
        )

    elif numeric_value < 0:

        direction = (
            "declined"
        )

    else:

        direction = (
            "was unchanged"
        )

    return (
        f"{label} {direction} "
        f"{abs(numeric_value):.2f}%"
    )


def format_pp_driver(
    label: str,
    value,
) -> str | None:

    numeric_value = (
        safe_float(
            value
        )
    )

    if numeric_value is None:

        return None

    if numeric_value > 0:

        direction = (
            "increased"
        )

    elif numeric_value < 0:

        direction = (
            "declined"
        )

    else:

        direction = (
            "was unchanged"
        )

    return (
        f"{label} {direction} "
        f"{abs(numeric_value):.2f} pp"
    )


def readable_diagnosis(
    diagnosis: str | None,
) -> str | None:

    if diagnosis is None:

        return None

    if (
        diagnosis
        in
        DIAGNOSIS_LABELS
    ):

        return (
            DIAGNOSIS_LABELS[
                diagnosis
            ]
        )

    return (
        diagnosis
        .replace(
            "_",
            " ",
        )
    )


# ============================================================
# DIAGNOSTIC ANSWER
# ============================================================

def diagnostic_answer(
    result: dict,
) -> str:

    event = (
        result[
            "data"
        ]
        [
            "event"
        ]
    )

    diagnostic = (
        event.get(
            "diagnostic",
            {},
        )
    )

    drivers = (
        diagnostic.get(
            "drivers",
            {},
        )
    )

    metric_label = (
        METRIC_LABELS.get(
            event[
                "metric"
            ],
            event[
                "metric"
            ],
        )
    )

    direction = (
        event.get(
            "direction"
        )
    )

    if (
        direction
        ==
        "increase"
    ):

        direction_phrase = (
            "increased"
        )

    elif (
        direction
        ==
        "decrease"
    ):

        direction_phrase = (
            "declined"
        )

    else:

        direction_phrase = (
            "was broadly unchanged"
        )

    answer = (
        f"{event['dimension_value']} "
        f"{metric_label} "
        f"{direction_phrase} "
        f"{format_change(event)} "
        "versus the comparison period."
    )

    diagnosis = (
        readable_diagnosis(
            diagnostic.get(
                "diagnosis"
            )
        )
    )

    if diagnosis:

        answer += (
            " The analysis indicates "
            f"{diagnosis}."
        )

    supporting = []

    driver_specs = [
        (
            format_pct_driver,
            "Units",
            drivers.get(
                "units_change_pct"
            ),
        ),

        (
            format_pct_driver,
            "Average selling price",
            drivers.get(
                "asp_change_pct"
            ),
        ),

        (
            format_pct_driver,
            "Cost per unit",
            drivers.get(
                "cost_per_unit_change_pct"
            ),
        ),

        (
            format_pp_driver,
            "Discount rate",
            drivers.get(
                "discount_change_pp"
            ),
        ),

        (
            format_pp_driver,
            "Stockout rate",
            drivers.get(
                "stockout_rate_change_pp"
            ),
        ),

        (
            format_pp_driver,
            "Gross margin",
            drivers.get(
                "margin_change_pp"
            ),
        ),
    ]

    for (
        formatter,
        label,
        value,
    ) in driver_specs:

        formatted = (
            formatter(
                label,
                value,
            )
        )

        if formatted:

            supporting.append(
                formatted
            )

    if supporting:

        answer += (
            " Supporting evidence: "
            +
            "; ".join(
                supporting
            )
            +
            "."
        )

    return answer


# ============================================================
# TARGET ANSWER
# ============================================================

def target_answer(
    result: dict,
) -> str:

    focus = (
        result.get(
            "focus"
        )
    )

    data = (
        result[
            "data"
        ]
    )

    if focus is not None:

        achievement = (
            safe_float(
                focus.get(
                    "sales_achievement_pct"
                )
            )
        )

        actual_sales = (
            safe_float(
                focus.get(
                    "actual_sales"
                )
            )
        )

        sales_target = (
            safe_float(
                focus.get(
                    "sales_target"
                )
            )
        )

        sales_gap = (
            safe_float(
                focus.get(
                    "sales_gap"
                )
            )
        )

        status = (
            focus.get(
                "status",
                "not available",
            )
        )

        severity = (
            focus.get(
                "severity",
                "informational",
            )
        )

        if achievement is not None:

            answer = (
                f"{focus['region']} achieved "
                f"{achievement:.1f}% "
                "of its sales target."
            )

        else:

            answer = (
                f"{focus['region']} target achievement "
                "could not be calculated."
            )

        if (
            actual_sales is not None
            and
            sales_target is not None
        ):

            answer += (
                " Actual sales were "
                f"{actual_sales:,.2f} "
                "against a target of "
                f"{sales_target:,.2f}."
            )

        if sales_gap is not None:

            if sales_gap < 0:

                answer += (
                    " This represents a shortfall "
                    f"of {abs(sales_gap):,.2f}."
                )

            elif sales_gap > 0:

                answer += (
                    " This represents an overachievement "
                    f"of {sales_gap:,.2f}."
                )

            else:

                answer += (
                    " Actual sales matched target."
                )

        if (
            status
            ==
            "missed"
        ):

            answer += (
                " This is classified as a "
                f"{severity}-severity target miss."
            )

        elif (
            status
            ==
            "at_risk"
        ):

            answer += (
                " Performance is classified as "
                f"at risk with {severity} severity."
            )

        elif (
            status
            ==
            "watch"
        ):

            answer += (
                " Performance is close to target "
                "but remains on the watch list."
            )

        elif (
            status
            ==
            "achieved"
        ):

            answer += (
                " The target was achieved."
            )

        return answer


    issues = (
        data.get(
            "material_target_issues",
            [],
        )
    )

    if not issues:

        return (
            "No material regional target issues "
            "were identified for the selected month."
        )

    top = (
        issues[
            0
        ]
    )

    achievement = (
        safe_float(
            top.get(
                "sales_achievement_pct"
            )
        )
    )

    achievement_text = (
        f"{achievement:.1f}%"
        if
        achievement is not None
        else
        "an unavailable percentage"
    )

    return (
        f"{len(issues)} region(s) have material "
        "target issues. The highest-priority issue "
        f"is {top['region']}, which achieved "
        f"{achievement_text} of its sales target."
    )


# ============================================================
# PROMOTION ANSWER
# ============================================================

def promotion_answer(
    result: dict,
) -> str:

    rows = (
        result[
            "data"
        ]
        .get(
            "results",
            [],
        )
    )

    if not rows:

        return (
            "No promotions were found "
            "in the selected period."
        )

    promotion = (
        rows[
            0
        ]
    )

    effectiveness = (
        promotion.get(
            "effectiveness",
            "not classified",
        )
    )

    diagnosis = (
        readable_diagnosis(
            promotion.get(
                "diagnosis"
            )
        )
    )

    answer = (
        f"{promotion['campaign_name']} "
        f"is classified as {effectiveness}."
    )

    evidence_parts = []

    driver_specs = [
        (
            format_pct_driver,
            "Units",
            promotion.get(
                "units_uplift_pct"
            ),
        ),

        (
            format_pct_driver,
            "Net sales",
            promotion.get(
                "revenue_uplift_pct"
            ),
        ),

        (
            format_pct_driver,
            "Average selling price",
            promotion.get(
                "asp_change_pct"
            ),
        ),

        (
            format_pp_driver,
            "Discount rate",
            promotion.get(
                "discount_change_pp"
            ),
        ),
    ]

    for (
        formatter,
        label,
        value,
    ) in driver_specs:

        formatted = (
            formatter(
                label,
                value,
            )
        )

        if formatted:

            evidence_parts.append(
                formatted
            )

    if evidence_parts:

        answer += (
            " Versus the pre-promotion baseline, "
            +
            "; ".join(
                evidence_parts
            )
            +
            "."
        )

    if diagnosis:

        answer += (
            " The analysis indicates "
            f"{diagnosis}."
        )

    return answer


# ============================================================
# LATEST CHANGES ANSWER
# ============================================================

def latest_changes_answer(
    result: dict,
) -> str:

    data = (
        result[
            "data"
        ]
    )

    summary = (
        data.get(
            "alert_summary",
            {},
        )
    )

    changes = (
        data.get(
            "top_changes",
            [],
        )
    )

    if not changes:

        return (
            "No material business changes were detected "
            "for the latest comparison period."
        )

    top = (
        changes[
            0
        ]
    )

    total_material = (
        summary.get(
            "total_material_changes",
            0,
        )
    )

    high_severity = (
        summary.get(
            "high",
            0,
        )
    )

    metric_label = (
        METRIC_LABELS.get(
            top.get(
                "metric"
            ),
            top.get(
                "metric",
                "metric",
            ),
        )
    )

    direction = (
        top.get(
            "direction"
        )
    )

    if direction == "increase":

        change_phrase = (
            "increased"
        )

    elif direction == "decrease":

        change_phrase = (
            "declined"
        )

    else:

        change_phrase = (
            "was broadly unchanged"
        )

    answer = (
        "The latest scan identified "
        f"{total_material} material changes, "
        f"including {high_severity} "
        "high-severity issues. "
        "The highest-ranked change is "
        f"{top['dimension_value']} "
        f"{metric_label}, which "
        f"{change_phrase} "
        f"{format_change(top)}."
    )

    diagnostic = (
        top.get(
            "diagnostic",
            {},
        )
    )

    diagnosis = (
        readable_diagnosis(
            diagnostic.get(
                "diagnosis"
            )
        )
    )

    if diagnosis:

        answer += (
            " The leading diagnostic is "
            f"{diagnosis}."
        )

    return answer


# ============================================================
# DETERMINISTIC ANSWER
# ============================================================

def deterministic_answer(
    intent: AnalystIntent,
    result: dict,
) -> str:

    tool = (
        result.get(
            "tool"
        )
    )

    if (
        tool
        ==
        "diagnose_business_change"
    ):

        return (
            diagnostic_answer(
                result
            )
        )

    if (
        tool
        ==
        "analyze_targets"
    ):

        return (
            target_answer(
                result
            )
        )

    if (
        tool
        ==
        "analyze_promotions"
    ):

        return (
            promotion_answer(
                result
            )
        )

    if (
        tool
        ==
        "detect_latest_business_changes"
    ):

        return (
            latest_changes_answer(
                result
            )
        )

    return (
        "I can currently analyze business changes, "
        "performance drivers, target achievement and "
        "promotion effectiveness. This question is "
        "outside the currently supported analytical scope."
    )


# ============================================================
# COMPACT EVIDENCE FOR OPTIONAL AI EXPLANATION
# ============================================================

def compact_evidence(
    result: dict,
) -> dict:

    tool = (
        result.get(
            "tool"
        )
    )

    if (
        tool
        ==
        "diagnose_business_change"
    ):

        return (
            result[
                "data"
            ]
        )

    if (
        tool
        ==
        "analyze_targets"
    ):

        return {
            "focus":
                result.get(
                    "focus"
                ),

            "material_target_issues":
                (
                    result[
                        "data"
                    ]
                    .get(
                        "material_target_issues",
                        [],
                    )[
                        :10
                    ]
                ),

            "summary":
                (
                    result[
                        "data"
                    ]
                    .get(
                        "summary",
                        {},
                    )
                ),
        }

    if (
        tool
        ==
        "analyze_promotions"
    ):

        return {
            "summary":
                (
                    result[
                        "data"
                    ]
                    .get(
                        "summary",
                        {},
                    )
                ),

            "results":
                (
                    result[
                        "data"
                    ]
                    .get(
                        "results",
                        [],
                    )[
                        :5
                    ]
                ),
        }

    if (
        tool
        ==
        "detect_latest_business_changes"
    ):

        return {
            "current_period":
                (
                    result[
                        "data"
                    ]
                    .get(
                        "current_period"
                    )
                ),

            "comparison_period":
                (
                    result[
                        "data"
                    ]
                    .get(
                        "comparison_period"
                    )
                ),

            "alert_summary":
                (
                    result[
                        "data"
                    ]
                    .get(
                        "alert_summary"
                    )
                ),

            "top_changes":
                (
                    result[
                        "data"
                    ]
                    .get(
                        "top_changes",
                        [],
                    )[
                        :10
                    ]
                ),
        }

    return result


# ============================================================
# OPTIONAL LOCAL-AI EXPLANATION
# ============================================================

def llm_answer(
    question: str,
    intent: AnalystIntent,
    result: dict,
) -> str:

    client = (
        get_llm_client()
    )

    model = (
        get_ollama_model()
    )

    evidence = (
        compact_evidence(
            result
        )
    )

    instructions = """
You are an enterprise business intelligence analyst.

Use only the VERIFIED analytical evidence supplied to you.

Rules:

1. Never invent numbers.
2. Never calculate new KPI values.
3. Never override deterministic diagnostics.
4. Never claim proof of causality.
5. Never mention SQL, JSON, APIs or implementation.
6. Never expose internal reasoning.
7. Lead with the business conclusion.
8. Keep the answer to 2-4 concise sentences.
"""

    payload = {
        "user_question":
            question,

        "parsed_intent":
            intent.model_dump(
                mode="json"
            ),

        "verified_evidence":
            evidence,
    }

    response = (
        client.chat(
            model=
                model,

            messages=[
                {
                    "role":
                        "system",

                    "content":
                        instructions,
                },

                {
                    "role":
                        "user",

                    "content":
                        json.dumps(
                            payload,
                            default=str,
                        ),
                },
            ],

            options={
                "temperature":
                    0.2,
            },

            think=
                False,

            stream=
                False,
        )
    )

    answer = (
        clean_llm_text(
            response.message.content
        )
    )

    if not answer:

        raise ValueError(
            "The local LLM returned an empty response."
        )

    return answer


# ============================================================
# PUBLIC RESPONSE COMPOSER
# ============================================================

def compose_answer(
    question: str,
    intent: AnalystIntent,
    result: dict,
    force_deterministic: bool = False,
) -> tuple[
    str,
    bool,
    list[str],
]:

    warnings = []

    fallback = (
        deterministic_answer(
            intent,
            result,
        )
    )


    # --------------------------------------------------------
    # FAST DEFAULT
    # --------------------------------------------------------

    if (
        force_deterministic
        or
        not settings.analyst_use_llm_response
    ):

        return (
            fallback,
            False,
            warnings,
        )


    # --------------------------------------------------------
    # OPTIONAL AI RESPONSE MODE
    # --------------------------------------------------------

    if llm_available():

        try:

            answer = (
                llm_answer(
                    question=
                        question,

                    intent=
                        intent,

                    result=
                        result,
                )
            )

            return (
                answer,
                True,
                warnings,
            )

        except Exception as error:

            warnings.append(
                (
                    "Local AI explanation failed; "
                    "the deterministic business response "
                    "was used. "
                    f"{type(error).__name__}: "
                    f"{str(error)}"
                )
            )

    return (
        fallback,
        False,
        warnings,
    )