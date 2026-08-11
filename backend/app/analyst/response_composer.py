import json

from .llm_client import (
    get_openai_client,
    get_openai_model,
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
# GENERAL FORMAT HELPERS
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


def format_number(
    value,
    decimals: int = 2,
) -> str:

    numeric_value = (
        safe_float(
            value
        )
    )

    if numeric_value is None:

        return (
            "not available"
        )

    return (
        f"{numeric_value:,.{decimals}f}"
    )


def format_percentage(
    value,
    decimals: int = 2,
) -> str:

    numeric_value = (
        safe_float(
            value
        )
    )

    if numeric_value is None:

        return (
            "not available"
        )

    return (
        f"{abs(numeric_value):.{decimals}f}%"
    )


def format_percentage_points(
    value,
    decimals: int = 2,
) -> str:

    numeric_value = (
        safe_float(
            value
        )
    )

    if numeric_value is None:

        return (
            "not available"
        )

    return (
        f"{abs(numeric_value):.{decimals}f} "
        "percentage points"
    )


def direction_word(
    value,
    increase_word: str = "increased",
    decrease_word: str = "declined",
    flat_word: str = "was broadly unchanged",
) -> str:

    numeric_value = (
        safe_float(
            value
        )
    )

    if numeric_value is None:

        return (
            "could not be evaluated"
        )

    if numeric_value > 0:

        return (
            increase_word
        )

    if numeric_value < 0:

        return (
            decrease_word
        )

    return (
        flat_word
    )


# ============================================================
# CHANGE DISPLAY
# ============================================================

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


# ============================================================
# DRIVER DISPLAY
# ============================================================

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


# ============================================================
# DIAGNOSIS DISPLAY
# ============================================================

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
# DETERMINISTIC DIAGNOSTIC ANSWER
# ============================================================

def diagnostic_answer(
    result: dict,
) -> str:

    data = (
        result[
            "data"
        ]
    )

    event = (
        data[
            "event"
        ]
    )

    diagnostic = (
        event.get(
            "diagnostic",
            {}
        )
    )

    drivers = (
        diagnostic.get(
            "drivers",
            {}
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

    event_direction = (
        event.get(
            "direction"
        )
    )

    if (
        event_direction
        ==
        "increase"
    ):

        direction_phrase = (
            "increased"
        )

    elif (
        event_direction
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
        f"versus the comparison period."
    )

    diagnosis = (
        diagnostic.get(
            "diagnosis"
        )
    )

    readable = (
        readable_diagnosis(
            diagnosis
        )
    )

    if readable:

        answer += (
            " The deterministic diagnostic "
            f"indicates {readable}."
        )

    supporting = []

    units_driver = (
        format_pct_driver(
            "Units",
            drivers.get(
                "units_change_pct"
            ),
        )
    )

    if units_driver:

        supporting.append(
            units_driver
        )

    asp_driver = (
        format_pct_driver(
            "Average selling price",
            drivers.get(
                "asp_change_pct"
            ),
        )
    )

    if asp_driver:

        supporting.append(
            asp_driver
        )

    cost_driver = (
        format_pct_driver(
            "Cost per unit",
            drivers.get(
                "cost_per_unit_change_pct"
            ),
        )
    )

    if cost_driver:

        supporting.append(
            cost_driver
        )

    discount_driver = (
        format_pp_driver(
            "Discount rate",
            drivers.get(
                "discount_change_pp"
            ),
        )
    )

    if discount_driver:

        supporting.append(
            discount_driver
        )

    stockout_driver = (
        format_pp_driver(
            "Stockout rate",
            drivers.get(
                "stockout_rate_change_pp"
            ),
        )
    )

    if stockout_driver:

        supporting.append(
            stockout_driver
        )

    margin_driver = (
        format_pp_driver(
            "Gross margin",
            drivers.get(
                "margin_change_pp"
            ),
        )
    )

    if margin_driver:

        supporting.append(
            margin_driver
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

        answer = (
            f"{focus['region']} achieved "
        )

        if achievement is not None:

            answer += (
                f"{achievement:.1f}% "
                "of its sales target."
            )

        else:

            answer += (
                "an unavailable percentage "
                "of its sales target."
            )

        if (
            actual_sales is not None
            and
            sales_target is not None
        ):

            answer += (
                f" Actual sales were "
                f"{actual_sales:,.2f} "
                f"against a target of "
                f"{sales_target:,.2f}."
            )

        if sales_gap is not None:

            if sales_gap < 0:

                answer += (
                    f" This represents a shortfall "
                    f"of {abs(sales_gap):,.2f}."
                )

            elif sales_gap > 0:

                answer += (
                    f" This represents an overachievement "
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
                f" This is classified as a "
                f"{severity}-severity target miss."
            )

        elif (
            status
            ==
            "at_risk"
        ):

            answer += (
                f" Performance is classified as "
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
            []
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

    top_achievement = (
        safe_float(
            top.get(
                "sales_achievement_pct"
            )
        )
    )

    if top_achievement is not None:

        achievement_text = (
            f"{top_achievement:.1f}%"
        )

    else:

        achievement_text = (
            "an unavailable percentage"
        )

    return (
        f"{len(issues)} region(s) have material "
        f"target issues. The highest-priority issue "
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
            []
        )
    )

    if not rows:

        return (
            "No promotions were found "
            "in the selected period."
        )

    # Current implementation returns one or more campaigns.
    # For the deterministic answer, lead with the first
    # matching campaign.
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

    units_uplift = (
        safe_float(
            promotion.get(
                "units_uplift_pct"
            )
        )
    )

    revenue_uplift = (
        safe_float(
            promotion.get(
                "revenue_uplift_pct"
            )
        )
    )

    asp_change = (
        safe_float(
            promotion.get(
                "asp_change_pct"
            )
        )
    )

    discount_change = (
        safe_float(
            promotion.get(
                "discount_change_pp"
            )
        )
    )

    answer = (
        f"{promotion['campaign_name']} "
        f"is classified as "
        f"{effectiveness}."
    )

    evidence_parts = []

    units_text = (
        format_pct_driver(
            "Units",
            units_uplift,
        )
    )

    if units_text:

        evidence_parts.append(
            units_text
        )

    revenue_text = (
        format_pct_driver(
            "Net sales",
            revenue_uplift,
        )
    )

    if revenue_text:

        evidence_parts.append(
            revenue_text
        )

    asp_text = (
        format_pct_driver(
            "Average selling price",
            asp_change,
        )
    )

    if asp_text:

        evidence_parts.append(
            asp_text
        )

    discount_text = (
        format_pp_driver(
            "Discount rate",
            discount_change,
        )
    )

    if discount_text:

        evidence_parts.append(
            discount_text
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
            " The deterministic diagnosis "
            f"is {diagnosis}."
        )

    return answer


# ============================================================
# LATEST CHANGE ANSWER
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
            {}
        )
    )

    changes = (
        data.get(
            "top_changes",
            []
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
        f"The latest scan identified "
        f"{total_material} material changes, "
        f"including {high_severity} "
        f"high-severity issues. "
        f"The highest-ranked change is "
        f"{top['dimension_value']} "
        f"{metric_label}, which "
        f"{change_phrase} "
        f"{format_change(top)}."
    )

    diagnostic = (
        top.get(
            "diagnostic",
            {}
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
            f" The leading diagnostic is "
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
# COMPACT VERIFIED EVIDENCE FOR LLM
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

    return (
        result
    )


# ============================================================
# LLM RESPONSE COMPOSER
# ============================================================

def llm_answer(
    question: str,
    intent: AnalystIntent,
    result: dict,
) -> str:

    client = (
        get_openai_client()
    )

    model = (
        get_openai_model()
    )

    evidence = (
        compact_evidence(
            result
        )
    )

    instructions = """
You are an enterprise business intelligence analyst.

Your task is to explain VERIFIED analytical evidence to a
business stakeholder in concise, decision-oriented language.

STRICT RULES:

1. Use only the verified evidence supplied in the input.
2. Never invent numbers, causes, entities or business facts.
3. Never calculate new KPI values yourself.
4. Never override deterministic calculations or diagnostics.
5. Clearly distinguish observed evidence from likely drivers.
6. Treat deterministic diagnoses as evidence-based likely
   explanations, not proof of causality.
7. Mention the most decision-relevant numbers.
8. If evidence is insufficient, explicitly say so.
9. Never mention JSON, APIs, SQL, Python, databases,
   tool routing, prompts or implementation details.
10. Avoid double-negative wording such as
    "declined by -29%".
11. Say "declined 29%" or "increased 29%" instead.
12. For percentage-point metrics, explicitly say
    "percentage points".
13. Keep the answer professional and suitable for an
    executive or commercial business user.
14. Lead with the key business conclusion.
15. Prefer 2-4 concise sentences unless the question
    clearly requires more detail.
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
        client.responses.create(
            model=
                model,

            instructions=
                instructions,

            input=
                json.dumps(
                    payload,
                    default=str,
                ),

            store=
                False,
        )
    )

    answer = (
        response.output_text
        .strip()
    )

    if not answer:

        raise ValueError(
            "OpenAI returned an empty response."
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

    # Always construct a verified deterministic answer first.
    # This guarantees that the core BI product continues to
    # work even if the external LLM is unavailable.
    fallback = (
        deterministic_answer(
            intent,
            result,
        )
    )

    if (
        not force_deterministic
        and
        llm_available()
    ):

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
                "OpenAI response generation failed; "
                "the deterministic business response "
                "was used instead. "
                f"{type(error).__name__}: "
                f"{str(error)}"
            )

    return (
        fallback,
        False,
        warnings,
    )