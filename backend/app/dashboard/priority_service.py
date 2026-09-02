from __future__ import annotations

import re

from datetime import date
from typing import Any


# ============================================================
# LABELS
# ============================================================

METRIC_LABELS = {

    "net_sales":
        "Net sales",

    "units_sold":
        "Units sold",

    "transactions":
        "Transactions",

    "gross_profit":
        "Gross profit",

    "margin_pct":
        "Gross margin",

    "avg_selling_price":
        "Average selling price",

    "discount_pct":
        "Discount rate",

    "cost_per_unit":
        "Cost per unit",

    "stockout_rate":
        "Stockout rate",
}


SEVERITY_WEIGHTS = {

    "high":
        60.0,

    "medium":
        35.0,

    "low":
        15.0,
}


CONFIDENCE_WEIGHTS = {

    "high":
        10.0,

    "medium":
        5.0,

    "low":
        0.0,
}


# ============================================================
# HELPERS
# ============================================================

def as_float(
    value: Any,
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


def fingerprint_part(
    value: str | None,
) -> str:

    value = (
        value
        or
        "unknown"
    )

    value = (
        value
        .strip()
        .lower()
    )

    value = re.sub(
        r"[^a-z0-9]+",
        "-",
        value,
    )

    return (
        value
        .strip(
            "-"
        )
        or
        "unknown"
    )


def build_fingerprint(
    insight_type: str,
    dimension: str,
    entity: str,
    metric: str,
    diagnosis: str | None,
) -> str:

    return "|".join(
        [
            fingerprint_part(
                insight_type
            ),

            fingerprint_part(
                dimension
            ),

            fingerprint_part(
                entity
            ),

            fingerprint_part(
                metric
            ),

            fingerprint_part(
                diagnosis
            ),
        ]
    )


def change_value(
    event: dict,
) -> float | None:

    pp = (
        as_float(
            event.get(
                "change_pp"
            )
        )
    )

    if pp is not None:
        return pp

    return (
        as_float(
            event.get(
                "change_pct"
            )
        )
    )


def formatted_change(
    event: dict,
) -> str:

    pp = (
        as_float(
            event.get(
                "change_pp"
            )
        )
    )

    if pp is not None:

        sign = (
            "+"
            if pp > 0
            else
            ""
        )

        return (
            f"{sign}{pp:.2f} pp"
        )


    pct = (
        as_float(
            event.get(
                "change_pct"
            )
        )
    )

    if pct is not None:

        sign = (
            "+"
            if pct > 0
            else
            ""
        )

        return (
            f"{sign}{pct:.2f}%"
        )

    return "Not available"


# ============================================================
# SCORE
# ============================================================

def event_score(
    event: dict,
) -> float:

    severity = (
        str(
            event.get(
                "severity",
                "low",
            )
        )
        .lower()
    )

    impact = (
        str(
            event.get(
                "impact",
                "contextual",
            )
        )
        .lower()
    )

    diagnostic = (
        event.get(
            "diagnostic"
        )
        or
        {}
    )

    confidence = (
        str(
            diagnostic.get(
                "confidence",
                "low",
            )
        )
        .lower()
    )

    metric = (
        event.get(
            "metric"
        )
    )

    direction = (
        event.get(
            "direction"
        )
    )

    score = (
        SEVERITY_WEIGHTS.get(
            severity,
            10.0,
        )
    )

    if impact == "negative":

        score += 25.0

    elif impact == "positive":

        score += 15.0


    score += (
        CONFIDENCE_WEIGHTS.get(
            confidence,
            0.0,
        )
    )


    magnitude = abs(
        change_value(
            event
        )
        or
        0.0
    )

    score += min(
        magnitude,
        20.0,
    )


    if (
        metric
        ==
        "margin_pct"
        and
        direction
        ==
        "decrease"
    ):

        score += 12.0


    elif (
        metric
        in {
            "net_sales",
            "gross_profit",
        }
        and
        direction
        ==
        "decrease"
    ):

        score += 8.0


    elif (
        metric
        ==
        "stockout_rate"
        and
        direction
        ==
        "increase"
    ):

        score += 10.0


    return round(
        score,
        2,
    )


# ============================================================
# TYPE
# ============================================================

def event_type(
    event: dict,
) -> str | None:

    impact = (
        str(
            event.get(
                "impact",
                "",
            )
        )
        .lower()
    )

    if impact == "negative":

        return "risk"


    if impact == "positive":

        return "opportunity"


    return None


# ============================================================
# TITLE
# ============================================================

def priority_title(
    entity: str,
    event: dict,
) -> str:

    metric = (
        event.get(
            "metric"
        )
    )

    direction = (
        event.get(
            "direction"
        )
    )


    if (
        metric
        ==
        "margin_pct"
        and
        direction
        ==
        "decrease"
    ):

        return (
            f"{entity} margin deterioration"
        )


    if (
        metric
        ==
        "gross_profit"
        and
        direction
        ==
        "decrease"
    ):

        return (
            f"{entity} profit decline"
        )


    if (
        metric
        ==
        "net_sales"
        and
        direction
        ==
        "decrease"
    ):

        return (
            f"{entity} sales decline"
        )


    if (
        metric
        ==
        "units_sold"
        and
        direction
        ==
        "decrease"
    ):

        return (
            f"{entity} volume decline"
        )


    if (
        metric
        ==
        "stockout_rate"
        and
        direction
        ==
        "increase"
    ):

        return (
            f"{entity} availability pressure"
        )


    if (
        direction
        ==
        "increase"
        and
        metric
        in {
            "net_sales",
            "gross_profit",
            "units_sold",
        }
    ):

        return (
            f"{entity} growth opportunity"
        )


    if (
        metric
        ==
        "margin_pct"
        and
        direction
        ==
        "increase"
    ):

        return (
            f"{entity} margin improvement"
        )


    label = (
        METRIC_LABELS.get(
            metric,
            str(
                metric
                or
                "performance"
            ),
        )
    )

    return (
        f"{entity} "
        f"{label.lower()} change"
    )


# ============================================================
# ACTION
# ============================================================

def recommended_action(
    diagnosis: str | None,
    event: dict,
) -> str:

    diagnosis = (
        diagnosis
        or
        ""
    )


    if diagnosis in {
        "discount_and_cost_pressure",
        "discount_pressure",
        "cost_pressure",
    }:

        return (
            "Review discount depth, pricing and cost movement; "
            "identify the products or channels contributing most "
            "to margin erosion."
        )


    if diagnosis in {
        "volume_and_availability",
        "availability_related_volume_pressure",
        "availability_deterioration",
    }:

        return (
            "Prioritize availability recovery by identifying the "
            "products, stores or channels with the highest "
            "stockout pressure and lost volume."
        )


    if diagnosis in {
        "price_led_growth",
        "pricing_change",
    }:

        return (
            "Validate whether price-led growth is sustainable and "
            "identify similar products or markets where the same "
            "pricing opportunity may exist."
        )


    if diagnosis in {
        "promotion_led_growth",
        "promotion_led_volume_growth",
    }:

        return (
            "Review promotion economics and identify where the "
            "successful mechanic can be repeated without creating "
            "unacceptable margin pressure."
        )


    if diagnosis == "volume_led_growth":

        return (
            "Identify the products, channels and locations driving "
            "the additional volume and assess where the growth can "
            "be replicated."
        )


    impact = (
        str(
            event.get(
                "impact",
                "",
            )
        )
        .lower()
    )


    if impact == "positive":

        return (
            "Identify the segments contributing most to the "
            "improvement and assess whether the pattern can be "
            "replicated elsewhere."
        )


    return (
        "Drill into product, channel and store contribution to "
        "isolate the strongest drivers before taking action."
    )


# ============================================================
# QUESTION
# ============================================================

def analyst_question(
    entity: str,
    event: dict,
) -> str:

    metric = (
        event.get(
            "metric"
        )
    )

    direction = (
        event.get(
            "direction"
        )
    )

    dimension = (
        event.get(
            "dimension"
        )
    )


    if dimension == "region":

        if (
            metric
            ==
            "margin_pct"
            and
            direction
            ==
            "decrease"
        ):

            return (
                f"What drove {entity} margin deterioration?"
            )


        if (
            metric
            ==
            "net_sales"
            and
            direction
            ==
            "decrease"
        ):

            return (
                f"Why did {entity} sales decline?"
            )


        return (
            f"What is driving performance in {entity}?"
        )


    return (
        f"What is driving the performance change for {entity}?"
    )


# ============================================================
# EVIDENCE
# ============================================================

def evidence_item(
    event: dict,
) -> dict:

    metric = (
        event.get(
            "metric"
        )
    )

    return {

        "metric":
            metric,

        "label":
            METRIC_LABELS.get(
                metric,
                str(
                    metric
                    or
                    "Metric"
                ),
            ),

        "change":
            formatted_change(
                event
            ),

        "direction":
            event.get(
                "direction"
            ),

        "severity":
            event.get(
                "severity"
            ),

        "impact":
            event.get(
                "impact"
            ),
    }


# ============================================================
# CHANGE PRIORITY
# ============================================================

def change_priority(
    events: list[dict],
) -> dict | None:

    relevant = [
        event
        for event
        in events
        if event_type(
            event
        )
        is not None
    ]


    if not relevant:

        return None


    ranked = sorted(
        relevant,
        key=
            event_score,
        reverse=True,
    )


    primary = (
        ranked[
            0
        ]
    )


    entity = str(
        primary.get(
            "dimension_value"
        )
        or
        "Business"
    )


    diagnostic = (
        primary.get(
            "diagnostic"
        )
        or
        {}
    )


    diagnosis = (
        diagnostic.get(
            "diagnosis"
        )
    )


    kind = (
        event_type(
            primary
        )
        or
        "risk"
    )


    dimension = str(
        primary.get(
            "dimension"
        )
        or
        "overall"
    )


    metric = str(
        primary.get(
            "metric"
        )
        or
        "net_sales"
    )


    fingerprint = (
        build_fingerprint(
            insight_type=
                kind,

            dimension=
                dimension,

            entity=
                entity,

            metric=
                metric,

            diagnosis=
                diagnosis,
        )
    )


    return {

        "fingerprint":
            fingerprint,

        "type":
            kind,

        "title":
            priority_title(
                entity,
                primary,
            ),

        "entity":
            entity,

        "dimension":
            dimension,

        "severity":
            primary.get(
                "severity"
            ),

        "priority_score":
            event_score(
                primary
            ),

        "primary_metric":
            metric,

        "primary_change":
            formatted_change(
                primary
            ),

        "direction":
            primary.get(
                "direction"
            ),

        "diagnosis":
            diagnosis,

        "confidence":
            diagnostic.get(
                "confidence"
            ),

        "evidence": [
            evidence_item(
                event
            )
            for event
            in ranked[
                :3
            ]
        ],

        "recommended_action":
            recommended_action(
                diagnosis,
                primary,
            ),

        "analyst_question":
            analyst_question(
                entity,
                primary,
            ),
    }


# ============================================================
# TARGET PRIORITY
# ============================================================

def target_priority(
    issue: dict,
    month_start: date | None,
) -> dict:

    region = str(
        issue.get(
            "region"
        )
        or
        "Region"
    )


    severity = str(
        issue.get(
            "severity"
        )
        or
        "medium"
    ).lower()


    achievement = (
        as_float(
            issue.get(
                "sales_achievement_pct"
            )
        )
    )


    gap = (
        as_float(
            issue.get(
                "sales_gap"
            )
        )
    )


    actual_sales = (
        as_float(
            issue.get(
                "actual_sales"
            )
        )
    )


    target = (
        as_float(
            issue.get(
                "sales_target"
            )
        )
    )


    score = (
        SEVERITY_WEIGHTS.get(
            severity,
            35.0,
        )
        +
        30.0
    )


    if achievement is not None:

        score += min(
            max(
                100.0
                -
                achievement,
                0.0,
            ),
            20.0,
        )


    evidence = []


    if achievement is not None:

        evidence.append(
            {
                "metric":
                    "target_attainment",

                "label":
                    "Target attainment",

                "change":
                    f"{achievement:.1f}%",

                "direction":
                    "below_target",

                "severity":
                    severity,

                "impact":
                    "negative",
            }
        )


    if gap is not None:

        evidence.append(
            {
                "metric":
                    "sales_gap",

                "label":
                    "Sales gap",

                "change":
                    f"{gap:,.2f}",

                "direction":
                    (
                        "shortfall"
                        if gap < 0
                        else
                        "overachievement"
                    ),

                "severity":
                    severity,

                "impact":
                    (
                        "negative"
                        if gap < 0
                        else
                        "positive"
                    ),
            }
        )


    if month_start:

        month_text = (
            month_start
            .strftime(
                "%B %Y"
            )
        )

        question = (
            f"How did {region} perform against target "
            f"in {month_text}?"
        )

    else:

        question = (
            f"How did {region} perform against target?"
        )


    diagnosis = (
        "target_underperformance"
    )


    fingerprint = (
        build_fingerprint(
            insight_type=
                "risk",

            dimension=
                "region",

            entity=
                region,

            metric=
                "target_attainment",

            diagnosis=
                diagnosis,
        )
    )


    return {

        "fingerprint":
            fingerprint,

        "type":
            "risk",

        "title":
            f"{region} target miss",

        "entity":
            region,

        "dimension":
            "region",

        "severity":
            severity,

        "priority_score":
            round(
                score,
                2,
            ),

        "primary_metric":
            "target_attainment",

        "primary_change":
            (
                f"{achievement:.1f}%"
                if achievement
                is not None
                else
                "Below target"
            ),

        "direction":
            "below_target",

        "diagnosis":
            diagnosis,

        "confidence":
            "high",

        "actual_sales":
            actual_sales,

        "sales_target":
            target,

        "sales_gap":
            gap,

        "evidence":
            evidence,

        "recommended_action":
            (
                "Identify the products, channels and locations "
                "contributing most to the target shortfall and "
                "prioritize the largest recoverable gaps."
            ),

        "analyst_question":
            question,
    }


# ============================================================
# PRIORITY ENGINE
# ============================================================

def build_business_priorities(
    intelligence: dict,
    target_payload: dict | None = None,
    target_month: date | None = None,
    max_risks: int = 3,
    max_opportunities: int = 2,
) -> dict:

    top_changes = (
        intelligence.get(
            "top_changes"
        )
        or
        []
    )


    groups: dict[
        tuple[str, str],
        list[dict],
    ] = {}


    for event in (
        top_changes
    ):

        dimension = str(
            event.get(
                "dimension"
            )
            or
            ""
        )


        entity = str(
            event.get(
                "dimension_value"
            )
            or
            ""
        )


        if (
            not dimension
            or
            not entity
            or
            dimension
            ==
            "overall"
        ):

            continue


        key = (
            dimension,
            entity,
        )


        groups.setdefault(
            key,
            [],
        ).append(
            event
        )


    priorities = []


    for events in (
        groups.values()
    ):

        priority = (
            change_priority(
                events
            )
        )


        if priority:

            priorities.append(
                priority
            )


    if target_payload:

        for issue in (
            target_payload.get(
                "material_target_issues"
            )
            or
            []
        ):

            priorities.append(
                target_priority(
                    issue=
                        issue,

                    month_start=
                        target_month,
                )
            )


    risks = sorted(
        [
            item
            for item
            in priorities
            if item[
                "type"
            ]
            ==
            "risk"
        ],
        key=
            lambda item:
                float(
                    item[
                        "priority_score"
                    ]
                ),
        reverse=True,
    )


    opportunities = sorted(
        [
            item
            for item
            in priorities
            if item[
                "type"
            ]
            ==
            "opportunity"
        ],
        key=
            lambda item:
                float(
                    item[
                        "priority_score"
                    ]
                ),
        reverse=True,
    )


    return {

        "risk_count":
            len(
                risks
            ),

        "opportunity_count":
            len(
                opportunities
            ),

        "risks":
            risks[
                :max_risks
            ],

        "opportunities":
            opportunities[
                :max_opportunities
            ],
    }