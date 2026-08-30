from __future__ import annotations

import json

from datetime import (
    date,
    timedelta,
)

from decimal import Decimal

from time import perf_counter

from typing import Any

from uuid import uuid4

from sqlalchemy import text

from ..database import engine


# ============================================================
# RECOMMENDATION QUESTION PHRASES
# ============================================================

RECOMMENDATION_PHRASES = (
    "how can we improve",
    "how do we improve",
    "what should we do",
    "what actions should we take",
    "what action should we take",
    "recommend actions",
    "recommend action",
    "recommended actions",
    "recommended action",
    "what should management focus on",
    "where should management focus",
    "what should i focus on",
    "where should we focus",
    "regions which require attention",
    "regions that require attention",
    "regions requiring attention",
    "areas which require attention",
    "areas that require attention",
    "areas requiring attention",
    "growth opportunity",
    "growth opportunities",
    "where can we grow",
    "where should we grow",
    "how should we scale",
)


# ============================================================
# METRIC LABELS
# ============================================================

METRIC_LABELS = {
    "net_sales":
        "net sales",

    "units_sold":
        "units sold",

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

    "target_attainment":
        "target attainment",
}


# ============================================================
# METRIC FAMILIES
#
# These let questions such as:
#
# "South margin deterioration"
#
# match a persisted:
#
# primary_metric = gross_profit
#
# without also bringing in unrelated target misses.
# ============================================================

PROFITABILITY_METRICS = {
    "gross_profit",
    "margin_pct",
    "discount_pct",
    "cost_per_unit",
}

TARGET_METRICS = {
    "target_attainment",
    "sales_target_achievement",
}

AVAILABILITY_METRICS = {
    "stockout_rate",
}

VOLUME_METRICS = {
    "units_sold",
    "transactions",
}

SALES_METRICS = {
    "net_sales",
    "units_sold",
    "transactions",
    "target_attainment",
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


def _safe_float(
    value: Any,
) -> float | None:

    if value is None:
        return None

    if isinstance(
        value,
        bool,
    ):
        return None

    if isinstance(
        value,
        (
            int,
            float,
            Decimal,
        ),
    ):
        return float(
            value
        )

    try:

        return float(
            str(value)
        )

    except (
        TypeError,
        ValueError,
    ):

        return None


def _json_safe(
    value: Any,
) -> Any:

    if isinstance(
        value,
        Decimal,
    ):

        return float(
            value
        )

    if isinstance(
        value,
        date,
    ):

        return value.isoformat()

    if isinstance(
        value,
        dict,
    ):

        return {
            str(key):
                _json_safe(
                    item
                )
            for (
                key,
                item,
            )
            in value.items()
        }

    if isinstance(
        value,
        (
            list,
            tuple,
        ),
    ):

        return [
            _json_safe(
                item
            )
            for item
            in value
        ]

    return value


# ============================================================
# QUESTION CLASSIFICATION
# ============================================================

def is_recommendation_question(
    question: str,
) -> bool:

    normalized = (
        _normalize_text(
            question
        )
    )

    if not normalized:
        return False

    if any(
        phrase
        in normalized
        for phrase
        in RECOMMENDATION_PHRASES
    ):
        return True

    improvement_language = any(
        phrase
        in normalized
        for phrase
        in (
            "improve sales",
            "improve performance",
            "improve margin",
            "improve profitability",
            "fix sales",
            "fix performance",
            "address the issue",
            "address these issues",
            "take action",
            "next action",
            "next steps",
            "scale growth",
        )
    )

    business_scope = any(
        phrase
        in normalized
        for phrase
        in (
            "region",
            "business",
            "sales",
            "margin",
            "profit",
            "target",
            "stockout",
            "availability",
            "performance",
            "growth",
        )
    )

    return (
        improvement_language
        and
        business_scope
    )


# ============================================================
# QUESTION MODE
# ============================================================

def _is_attention_question(
    question: str,
) -> bool:

    normalized = (
        _normalize_text(
            question
        )
    )

    return any(
        phrase
        in normalized
        for phrase
        in (
            "require attention",
            "requires attention",
            "requiring attention",
            "need attention",
            "needs attention",
            "underperform",
            "under-performing",
            "problem areas",
            "problem regions",
            "issues",
            "risks",
        )
    )


def _is_opportunity_question(
    question: str,
) -> bool:

    normalized = (
        _normalize_text(
            question
        )
    )

    opportunity_language = any(
        phrase
        in normalized
        for phrase
        in (
            "growth opportunity",
            "growth opportunities",
            "where can we grow",
            "where should we grow",
            "scale growth",
            "scale the growth",
            "expand growth",
            "positive opportunity",
            "opportunities",
        )
    )

    return (
        opportunity_language
        and
        not _is_attention_question(
            question
        )
    )


# ============================================================
# CURRENT DATA PERIOD
# ============================================================

def _get_latest_data_date() -> date | None:

    query = text(
        """
        SELECT
            MAX(date_id)
        FROM
            analytics.fact_sales_daily;
        """
    )

    with engine.connect() as connection:

        return (
            connection
            .execute(
                query
            )
            .scalar_one_or_none()
        )


def _month_context() -> dict:

    latest_date = (
        _get_latest_data_date()
    )

    if latest_date is None:

        return {
            "current_start":
                None,

            "current_end":
                None,

            "comparison_start":
                None,

            "comparison_end":
                None,
        }

    current_start = (
        latest_date.replace(
            day=1
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
        comparison_end.replace(
            day=1
        )
    )

    return {
        "current_start":
            current_start.isoformat(),

        "current_end":
            latest_date.isoformat(),

        "comparison_start":
            comparison_start.isoformat(),

        "comparison_end":
            comparison_end.isoformat(),
    }


# ============================================================
# AVAILABLE REGIONS
# ============================================================

def get_available_regions() -> list[str]:

    query = text(
        """
        SELECT DISTINCT
            region
        FROM
            analytics.dim_store
        WHERE
            region IS NOT NULL
        ORDER BY
            region;
        """
    )

    with engine.connect() as connection:

        return [
            str(value)
            for value
            in (
                connection
                .execute(
                    query
                )
                .scalars()
                .all()
            )
        ]


def find_requested_region(
    question: str,
) -> str | None:

    normalized_question = (
        _normalize_text(
            question
        )
    )

    available_regions = (
        get_available_regions()
    )

    for region in available_regions:

        normalized_region = (
            _normalize_text(
                region
            )
        )

        if (
            normalized_region
            and
            normalized_region
            in normalized_question
        ):

            return region

    aliases = {
        "northern":
            "North",

        "southern":
            "South",

        "eastern":
            "East",

        "western":
            "West",

        "central":
            "Central",
    }

    available_lookup = {
        _normalize_text(
            region
        ):
            region
        for region
        in available_regions
    }

    for (
        alias,
        canonical,
    ) in aliases.items():

        if (
            alias
            in normalized_question
        ):

            return (
                available_lookup.get(
                    canonical.lower()
                )
            )

    return None


# ============================================================
# QUESTION FOCUS
# ============================================================

def _question_focus(
    question: str,
) -> str | None:

    normalized = (
        _normalize_text(
            question
        )
    )

    if any(
        phrase
        in normalized
        for phrase
        in (
            "stockout",
            "stock out",
            "availability",
            "out of stock",
        )
    ):

        return "availability"

    if any(
        phrase
        in normalized
        for phrase
        in (
            "margin",
            "profitability",
            "gross profit",
            "profit decline",
            "profit deterioration",
        )
    ):

        return "profitability"

    if (
        "target"
        in normalized
    ):

        return "target"

    if any(
        phrase
        in normalized
        for phrase
        in (
            "volume",
            "units",
            "transactions",
        )
    ):

        return "volume"

    if any(
        phrase
        in normalized
        for phrase
        in (
            "sales",
            "revenue",
        )
    ):

        return "sales"

    return None


def _metric_hint(
    question: str,
) -> str | None:

    focus = (
        _question_focus(
            question
        )
    )

    if (
        focus
        ==
        "availability"
    ):

        return "stockout_rate"

    if (
        focus
        ==
        "profitability"
    ):

        return "margin_pct"

    if (
        focus
        ==
        "target"
    ):

        return "target_attainment"

    if (
        focus
        ==
        "volume"
    ):

        return "units_sold"

    if (
        focus
        ==
        "sales"
    ):

        return "net_sales"

    return None


# ============================================================
# LOAD ACTIVE PERSISTED INSIGHTS
# ============================================================

def load_active_insights(
    limit: int = 100,
) -> list[dict]:

    safe_limit = max(
        1,
        min(
            int(limit),
            500,
        ),
    )

    query = text(
        """
        SELECT
            *
        FROM
            analytics.business_insights
        WHERE
            UPPER(
                COALESCE(
                    lifecycle_status,
                    ''
                )
            )
            <>
            'RESOLVED'
        ORDER BY
            priority_score DESC NULLS LAST,
            insight_id DESC
        LIMIT
            :limit;
        """
    )

    with engine.connect() as connection:

        rows = (
            connection
            .execute(
                query,
                {
                    "limit":
                        safe_limit,
                },
            )
            .mappings()
            .all()
        )

    return [
        dict(row)
        for row
        in rows
    ]


# ============================================================
# PAYLOAD NORMALIZATION
# ============================================================

def _payload_dict(
    insight: dict,
) -> dict:

    payload = (
        insight.get(
            "payload"
        )
    )

    if isinstance(
        payload,
        dict,
    ):

        return payload

    if isinstance(
        payload,
        str,
    ):

        try:

            parsed = json.loads(
                payload
            )

            if isinstance(
                parsed,
                dict,
            ):

                return parsed

        except json.JSONDecodeError:

            pass

    return {}


# ============================================================
# RECURSIVE PAYLOAD SEARCH
# ============================================================

def _find_value_recursive(
    value: Any,
    key_names: set[str],
) -> Any:

    normalized_keys = {
        key.lower()
        for key
        in key_names
    }

    if isinstance(
        value,
        dict,
    ):

        for (
            key,
            item,
        ) in value.items():

            if (
                str(key)
                .lower()
                in normalized_keys
            ):

                return item

        for item in (
            value.values()
        ):

            result = (
                _find_value_recursive(
                    item,
                    key_names,
                )
            )

            if result is not None:

                return result

    elif isinstance(
        value,
        list,
    ):

        for item in value:

            result = (
                _find_value_recursive(
                    item,
                    key_names,
                )
            )

            if result is not None:

                return result

    return None


def _find_numeric(
    payload: dict,
    *keys: str,
) -> float | None:

    value = (
        _find_value_recursive(
            payload,
            set(keys),
        )
    )

    return (
        _safe_float(
            value
        )
    )


def _find_text(
    payload: dict,
    *keys: str,
) -> str | None:

    value = (
        _find_value_recursive(
            payload,
            set(keys),
        )
    )

    if value is None:

        return None

    if isinstance(
        value,
        (
            dict,
            list,
        ),
    ):

        return None

    text_value = (
        str(value)
        .strip()
    )

    if not text_value:

        return None

    return text_value


# ============================================================
# INSIGHT TYPE HELPERS
# ============================================================

def _is_opportunity(
    insight: dict,
) -> bool:

    insight_type = (
        _normalize_text(
            insight.get(
                "insight_type"
            )
        )
    )

    title = (
        _normalize_text(
            insight.get(
                "title"
            )
        )
    )

    fingerprint = (
        _normalize_text(
            insight.get(
                "fingerprint"
            )
        )
    )

    return (
        insight_type
        in {
            "opportunity",
            "positive",
            "growth",
        }
        or
        "opportunity"
        in title
        or
        "opportunity"
        in fingerprint
    )


def _is_risk(
    insight: dict,
) -> bool:

    return (
        not _is_opportunity(
            insight
        )
    )


# ============================================================
# DIAGNOSIS EXTRACTION
# ============================================================

def _diagnosis(
    insight: dict,
    payload: dict,
) -> str:

    payload_diagnosis = (
        _find_text(
            payload,
            "diagnosis",
            "root_cause",
            "root_cause_code",
        )
    )

    if payload_diagnosis:

        normalized = (
            payload_diagnosis
            .strip()
            .lower()
            .replace(
                "-",
                "_",
            )
            .replace(
                " ",
                "_",
            )
        )

        return normalized

    fingerprint = (
        _normalize_text(
            insight.get(
                "fingerprint"
            )
        )
        .replace(
            "-",
            "_",
        )
    )

    known_diagnoses = (
        "volume_and_availability",
        "discount_and_cost_pressure",
        "price_led_growth",
        "volume_led_growth",
        "promotion_led_volume_growth",
        "target_underperformance",
        "volume_decline",
        "pricing_change",
        "mixed_or_unexplained",
        "mixed_unexplained",
    )

    for diagnosis in (
        known_diagnoses
    ):

        if (
            diagnosis
            in fingerprint
        ):

            if (
                diagnosis
                ==
                "mixed_unexplained"
            ):

                return (
                    "mixed_or_unexplained"
                )

            return diagnosis

    return (
        "mixed_or_unexplained"
    )


# ============================================================
# EVIDENCE FORMATTING
# ============================================================

def _format_pct_change(
    label: str,
    value: float,
) -> str:

    if value > 0:

        return (
            f"{label} increased "
            f"{abs(value):.2f}%."
        )

    if value < 0:

        return (
            f"{label} declined "
            f"{abs(value):.2f}%."
        )

    return (
        f"{label} was unchanged."
    )


def _format_pp_change(
    label: str,
    value: float,
) -> str:

    if value > 0:

        return (
            f"{label} increased "
            f"{abs(value):.2f} pp."
        )

    if value < 0:

        return (
            f"{label} declined "
            f"{abs(value):.2f} pp."
        )

    return (
        f"{label} was unchanged."
    )


def _build_evidence(
    insight: dict,
    payload: dict,
) -> list[str]:

    evidence: list[str] = []

    title = (
        str(
            insight.get(
                "title"
            )
            or
            ""
        )
        .strip()
    )

    if title:

        evidence.append(
            title
        )

    primary_metric = (
        str(
            insight.get(
                "primary_metric"
            )
            or
            ""
        )
        .strip()
    )

    metric_label = (
        METRIC_LABELS.get(
            primary_metric,
            primary_metric.replace(
                "_",
                " ",
            ),
        )
        if primary_metric
        else
        "Primary metric"
    )

    metric_change = (
        _find_numeric(
            payload,
            "change_pct",
            "metric_change_pct",
            "primary_change_pct",
        )
    )

    if metric_change is not None:

        evidence.append(
            _format_pct_change(
                metric_label.capitalize(),
                metric_change,
            )
        )

    units_change = (
        _find_numeric(
            payload,
            "units_change_pct",
        )
    )

    if (
        units_change is not None
        and
        primary_metric
        !=
        "units_sold"
    ):

        evidence.append(
            _format_pct_change(
                "Units",
                units_change,
            )
        )

    stockout_change = (
        _find_numeric(
            payload,
            "stockout_rate_change_pp",
            "stockout_change_pp",
        )
    )

    if stockout_change is not None:

        evidence.append(
            _format_pp_change(
                "Stockout rate",
                stockout_change,
            )
        )

    margin_change = (
        _find_numeric(
            payload,
            "margin_change_pp",
            "margin_pct_change_pp",
        )
    )

    if margin_change is not None:

        evidence.append(
            _format_pp_change(
                "Gross margin",
                margin_change,
            )
        )

    discount_change = (
        _find_numeric(
            payload,
            "discount_change_pp",
            "discount_pct_change_pp",
        )
    )

    if discount_change is not None:

        evidence.append(
            _format_pp_change(
                "Discount rate",
                discount_change,
            )
        )

    achievement = (
        _find_numeric(
            payload,
            "sales_achievement_pct",
            "achievement_pct",
        )
    )

    if achievement is not None:

        evidence.append(
            (
                "Sales target achievement "
                f"was {achievement:.1f}%."
            )
        )

    severity = (
        str(
            insight.get(
                "severity"
            )
            or
            ""
        )
        .strip()
        .lower()
    )

    priority_score = (
        _safe_float(
            insight.get(
                "priority_score"
            )
        )
    )

    if (
        severity
        and
        priority_score is not None
    ):

        evidence.append(
            (
                f"Priority severity is "
                f"{severity}; priority score "
                f"is {priority_score:.1f}."
            )
        )

    elif severity:

        evidence.append(
            (
                f"Priority severity is "
                f"{severity}."
            )
        )

    return evidence[
        :5
    ]


# ============================================================
# RECOMMENDATION POLICY
# ============================================================

def _recommendation_policy(
    insight: dict,
    diagnosis: str,
) -> dict:

    title = (
        _normalize_text(
            insight.get(
                "title"
            )
        )
    )

    fingerprint = (
        _normalize_text(
            insight.get(
                "fingerprint"
            )
        )
    )

    metric = (
        _normalize_text(
            insight.get(
                "primary_metric"
            )
        )
    )

    insight_type = (
        _normalize_text(
            insight.get(
                "insight_type"
            )
        )
    )

    combined = (
        f"{title} "
        f"{fingerprint} "
        f"{metric} "
        f"{diagnosis} "
        f"{insight_type}"
    )

    # --------------------------------------------------------
    # OPPORTUNITIES FIRST
    #
    # This must happen before generic "volume" rules.
    #
    # Otherwise:
    #
    # volume_led_growth
    #
    # incorrectly matches the old volume-decline policy.
    # --------------------------------------------------------

    if (
        _is_opportunity(
            insight
        )
        or
        diagnosis
        in {
            "volume_led_growth",
            "price_led_growth",
            "promotion_led_volume_growth",
        }
    ):

        return {
            "management_focus":
                (
                    "Protect and selectively scale the "
                    "proven growth driver while preserving "
                    "margin and availability."
                ),

            "actions": [
                (
                    "Identify the products, stores and "
                    "channels contributing most to the growth."
                ),
                (
                    "Validate that the growth is supported by "
                    "healthy margin, availability and repeatable "
                    "demand rather than a one-off effect."
                ),
                (
                    "Scale the strongest commercial pattern "
                    "selectively and monitor whether the uplift "
                    "persists in the next period."
                ),
            ],

            "expected_kpis": [
                "net_sales",
                "units_sold",
                "gross_profit",
                "margin_pct",
                "stockout_rate",
            ],

            "action_type":
                "growth",
        }

    # --------------------------------------------------------
    # TARGET MISS
    # --------------------------------------------------------

    if (
        "target"
        in combined
    ):

        return {
            "management_focus":
                (
                    "Close the highest-value target gap before "
                    "expanding activity elsewhere."
                ),

            "actions": [
                (
                    "Identify the products, stores or channels "
                    "contributing most to the target shortfall."
                ),
                (
                    "Prioritize recovery activity against the "
                    "largest commercially relevant gaps."
                ),
                (
                    "Track target attainment, net sales and "
                    "units after each intervention."
                ),
            ],

            "expected_kpis": [
                "target_attainment",
                "net_sales",
                "units_sold",
            ],

            "action_type":
                "recovery",
        }

    # --------------------------------------------------------
    # AVAILABILITY
    # --------------------------------------------------------

    if (
        "availability"
        in combined
        or
        "stockout"
        in combined
    ):

        return {
            "management_focus":
                (
                    "Restore availability before adding "
                    "incremental demand pressure."
                ),

            "actions": [
                (
                    "Identify the products and stores "
                    "contributing most to the availability "
                    "deterioration."
                ),
                (
                    "Review replenishment cadence and inventory "
                    "coverage for the affected area."
                ),
                (
                    "Track stockout rate, units and net sales "
                    "after availability actions are implemented."
                ),
            ],

            "expected_kpis": [
                "stockout_rate",
                "units_sold",
                "net_sales",
            ],

            "action_type":
                "recovery",
        }

    # --------------------------------------------------------
    # PROFITABILITY
    #
    # gross_profit is intentionally included so a persisted
    # "South profit decline" does not fall into the generic
    # mixed/unexplained policy.
    # --------------------------------------------------------

    if (
        "margin"
        in combined
        or
        "gross_profit"
        in combined
        or
        "profit decline"
        in combined
        or
        "profitability"
        in combined
        or
        "discount"
        in combined
        or
        "cost_pressure"
        in combined
    ):

        return {
            "management_focus":
                (
                    "Protect profitability by isolating the "
                    "commercial sources of margin and profit "
                    "pressure."
                ),

            "actions": [
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

    # --------------------------------------------------------
    # PROMOTION
    # --------------------------------------------------------

    if (
        "promotion"
        in combined
    ):

        return {
            "management_focus":
                (
                    "Protect profitable promotional growth "
                    "rather than optimizing volume alone."
                ),

            "actions": [
                (
                    "Compare promotional volume uplift with "
                    "revenue and margin quality."
                ),
                (
                    "Identify where the promotion generated "
                    "incremental demand rather than simple "
                    "discounting."
                ),
                (
                    "Scale the mechanic selectively where the "
                    "commercial evidence remains positive."
                ),
            ],

            "expected_kpis": [
                "units_sold",
                "net_sales",
                "margin_pct",
                "discount_pct",
            ],

            "action_type":
                "growth",
        }

    # --------------------------------------------------------
    # PRICE
    # --------------------------------------------------------

    if (
        "pricing_change"
        in combined
    ):

        return {
            "management_focus":
                (
                    "Determine whether pricing is supporting "
                    "revenue without damaging underlying demand."
                ),

            "actions": [
                (
                    "Compare selling-price movement with units "
                    "and transaction trends."
                ),
                (
                    "Identify whether the effect is concentrated "
                    "in specific products or channels."
                ),
                (
                    "Monitor revenue and margin quality before "
                    "extending the pricing approach."
                ),
            ],

            "expected_kpis": [
                "avg_selling_price",
                "units_sold",
                "net_sales",
                "transactions",
                "margin_pct",
            ],

            "action_type":
                "pricing",
        }

    # --------------------------------------------------------
    # VOLUME RISK
    # --------------------------------------------------------

    if (
        "volume"
        in combined
    ):

        return {
            "management_focus":
                (
                    "Recover underlying demand or execution "
                    "volume before relying on price to offset "
                    "the decline."
                ),

            "actions": [
                (
                    "Identify the products, stores and channels "
                    "driving the largest volume decline."
                ),
                (
                    "Separate demand weakness from execution "
                    "and availability problems."
                ),
                (
                    "Track units, transactions and net sales "
                    "through the recovery period."
                ),
            ],

            "expected_kpis": [
                "units_sold",
                "transactions",
                "net_sales",
            ],

            "action_type":
                "recovery",
        }

    # --------------------------------------------------------
    # GENERIC / MIXED
    # --------------------------------------------------------

    return {
        "management_focus":
            (
                "Decompose the issue into volume, price, "
                "availability, discount and cost drivers "
                "before taking broad action."
            ),

        "actions": [
            (
                "Investigate the largest contributors behind "
                "the priority issue."
            ),
            (
                "Separate demand, pricing, availability and "
                "profitability effects."
            ),
            (
                "Create an owned action only after the "
                "dominant driver is supported by evidence."
            ),
        ],

        "expected_kpis": [
            "net_sales",
            "units_sold",
            "margin_pct",
            "stockout_rate",
        ],

        "action_type":
            "investigation",
    }


# ============================================================
# METRIC-FAMILY MATCHING
# ============================================================

def _matches_question_focus(
    insight: dict,
    focus: str | None,
) -> bool:

    if focus is None:

        return True

    metric = (
        _normalize_text(
            insight.get(
                "primary_metric"
            )
        )
    )

    title = (
        _normalize_text(
            insight.get(
                "title"
            )
        )
    )

    if (
        focus
        ==
        "profitability"
    ):

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

    if (
        focus
        ==
        "target"
    ):

        return (
            metric
            in TARGET_METRICS
            or
            "target"
            in title
        )

    if (
        focus
        ==
        "availability"
    ):

        return (
            metric
            in AVAILABILITY_METRICS
            or
            "stockout"
            in title
            or
            "availability"
            in title
        )

    if (
        focus
        ==
        "volume"
    ):

        return (
            metric
            in VOLUME_METRICS
            or
            "volume"
            in title
            or
            "units"
            in title
        )

    # Generic sales requests are intentionally broad.
    # We do NOT filter them strictly because profitability,
    # target and availability issues can all affect sales.

    if (
        focus
        ==
        "sales"
    ):

        return True

    return True


# ============================================================
# SEVERITY WEIGHT
# ============================================================

def _severity_weight(
    insight: dict,
) -> float:

    severity = (
        _normalize_text(
            insight.get(
                "severity"
            )
        )
    )

    weights = {
        "critical":
            25.0,

        "high":
            20.0,

        "medium":
            10.0,

        "low":
            0.0,
    }

    return (
        weights.get(
            severity,
            0.0,
        )
    )


# ============================================================
# INSIGHT SCORING
# ============================================================

def _ranking_score(
    insight: dict,
    question: str,
    requested_region: str | None,
    focus: str | None,
) -> float:

    score = (
        _safe_float(
            insight.get(
                "priority_score"
            )
        )
        or
        0.0
    )

    score += (
        _severity_weight(
            insight
        )
    )

    dimension = (
        _normalize_text(
            insight.get(
                "dimension"
            )
        )
    )

    dimension_value = (
        _normalize_text(
            insight.get(
                "dimension_value"
            )
        )
    )

    normalized_question = (
        _normalize_text(
            question
        )
    )

    if (
        "region"
        in normalized_question
        and
        dimension
        ==
        "region"
    ):

        score += 25.0

    if (
        requested_region
        and
        dimension_value
        ==
        _normalize_text(
            requested_region
        )
    ):

        score += 100.0

    if (
        _matches_question_focus(
            insight,
            focus,
        )
    ):

        score += 15.0

    if (
        _is_attention_question(
            question
        )
        and
        _is_risk(
            insight
        )
    ):

        score += 30.0

    if (
        _is_opportunity_question(
            question
        )
        and
        _is_opportunity(
            insight
        )
    ):

        score += 30.0

    return score


# ============================================================
# SELECT DECISION-RELEVANT INSIGHTS
# ============================================================

def _select_insights(
    insights: list[dict],
    question: str,
    limit: int,
) -> tuple[
    list[dict],
    str | None,
    str,
]:

    requested_region = (
        find_requested_region(
            question
        )
    )

    focus = (
        _question_focus(
            question
        )
    )

    normalized_question = (
        _normalize_text(
            question
        )
    )

    candidates = list(
        insights
    )

    selection_mode = (
        "general"
    )

    # --------------------------------------------------------
    # REGION FILTER
    # --------------------------------------------------------

    if requested_region:

        region_candidates = [
            insight
            for insight
            in candidates
            if (
                _normalize_text(
                    insight.get(
                        "dimension"
                    )
                )
                ==
                "region"
                and
                _normalize_text(
                    insight.get(
                        "dimension_value"
                    )
                )
                ==
                _normalize_text(
                    requested_region
                )
            )
        ]

        if region_candidates:

            candidates = (
                region_candidates
            )

        selection_mode = (
            "specific_region"
        )

    elif (
        "region"
        in normalized_question
    ):

        region_candidates = [
            insight
            for insight
            in candidates
            if (
                _normalize_text(
                    insight.get(
                        "dimension"
                    )
                )
                ==
                "region"
            )
        ]

        if region_candidates:

            candidates = (
                region_candidates
            )

        selection_mode = (
            "regional"
        )

    # --------------------------------------------------------
    # RISK / OPPORTUNITY MODE
    #
    # "regions requiring attention"
    # must NOT include North growth opportunity.
    # --------------------------------------------------------

    if (
        _is_attention_question(
            question
        )
    ):

        risk_candidates = [
            insight
            for insight
            in candidates
            if _is_risk(
                insight
            )
        ]

        if risk_candidates:

            candidates = (
                risk_candidates
            )

        selection_mode = (
            "risk_attention"
        )

    elif (
        _is_opportunity_question(
            question
        )
    ):

        opportunity_candidates = [
            insight
            for insight
            in candidates
            if _is_opportunity(
                insight
            )
        ]

        if opportunity_candidates:

            candidates = (
                opportunity_candidates
            )

        selection_mode = (
            "growth_opportunity"
        )

    # --------------------------------------------------------
    # SPECIFIC BUSINESS FOCUS
    #
    # For a specific-region question such as:
    #
    # "South margin deterioration"
    #
    # use profitability-relevant South insights rather than
    # returning South target miss as well.
    # --------------------------------------------------------

    strict_focuses = {
        "profitability",
        "target",
        "availability",
        "volume",
    }

    if (
        focus
        in strict_focuses
    ):

        focused_candidates = [
            insight
            for insight
            in candidates
            if (
                _matches_question_focus(
                    insight,
                    focus,
                )
            )
        ]

        if focused_candidates:

            candidates = (
                focused_candidates
            )

    # --------------------------------------------------------
    # RANK
    # --------------------------------------------------------

    ranked = sorted(
        candidates,
        key=lambda insight: (
            _ranking_score(
                insight,
                question,
                requested_region,
                focus,
            )
        ),
        reverse=True,
    )

    selected: list[dict] = []

    seen_region_scopes: set[str] = set()

    for insight in ranked:

        dimension = (
            _normalize_text(
                insight.get(
                    "dimension"
                )
            )
        )

        dimension_value = (
            _normalize_text(
                insight.get(
                    "dimension_value"
                )
            )
        )

        # For broad regional questions we want one primary
        # management priority per region.

        if (
            not requested_region
            and
            dimension
            ==
            "region"
            and
            dimension_value
        ):

            scope_key = (
                f"region|"
                f"{dimension_value}"
            )

            if (
                scope_key
                in seen_region_scopes
            ):

                continue

            seen_region_scopes.add(
                scope_key
            )

        selected.append(
            insight
        )

        if (
            len(selected)
            >=
            limit
        ):

            break

    return (
        selected,
        requested_region,
        selection_mode,
    )


# ============================================================
# BUILD ONE RECOMMENDATION
# ============================================================

def _build_recommendation(
    insight: dict,
) -> dict:

    payload = (
        _payload_dict(
            insight
        )
    )

    diagnosis = (
        _diagnosis(
            insight,
            payload,
        )
    )

    policy = (
        _recommendation_policy(
            insight,
            diagnosis,
        )
    )

    evidence = (
        _build_evidence(
            insight,
            payload,
        )
    )

    dimension = (
        insight.get(
            "dimension"
        )
    )

    dimension_value = (
        insight.get(
            "dimension_value"
        )
    )

    severity = (
        insight.get(
            "severity"
        )
    )

    priority_score = (
        _safe_float(
            insight.get(
                "priority_score"
            )
        )
    )

    lifecycle_status = (
        insight.get(
            "lifecycle_status"
        )
    )

    title = (
        str(
            insight.get(
                "title"
            )
            or
            "Business priority"
        )
        .strip()
    )

    action_title_scope = (
        str(
            dimension_value
        )
        .strip()
        if dimension_value
        else
        "Business"
    )

    return {
        "insight_id":
            insight.get(
                "insight_id"
            ),

        "title":
            title,

        "insight_type":
            insight.get(
                "insight_type"
            ),

        "dimension":
            dimension,

        "dimension_value":
            dimension_value,

        "primary_metric":
            insight.get(
                "primary_metric"
            ),

        "severity":
            severity,

        "priority_score":
            priority_score,

        "lifecycle_status":
            lifecycle_status,

        "diagnosis":
            diagnosis,

        "management_focus":
            policy[
                "management_focus"
            ],

        "evidence":
            evidence,

        "recommended_actions":
            policy[
                "actions"
            ],

        "expected_kpis":
            policy[
                "expected_kpis"
            ],

        "action_type":
            policy[
                "action_type"
            ],

        "action_template": {
            "title":
                (
                    f"{action_title_scope}: "
                    f"{policy['management_focus']}"
                ),

            "owner":
                None,

            "notes":
                (
                    "Generated from verified business "
                    "intelligence evidence. Review and "
                    "assign an owner before execution."
                ),
        },

        "period_start":
            _json_safe(
                insight.get(
                    "period_start"
                )
            ),

        "period_end":
            _json_safe(
                insight.get(
                    "period_end"
                )
            ),
    }


# ============================================================
# ANSWER COMPOSER
#
# ASCII punctuation is used intentionally.
# This avoids the Windows PowerShell mojibake seen as:
#
# South â ...
# ============================================================

def _compose_answer(
    recommendations: list[dict],
    requested_region: str | None,
    selection_mode: str,
) -> str:

    if not recommendations:

        return (
            "There are currently no active persisted "
            "business priorities matching this request. "
            "Run the latest intelligence analysis after "
            "refreshing the data, then ask the question again."
        )

    if requested_region:

        if (
            selection_mode
            ==
            "growth_opportunity"
        ):

            opening = (
                f"{requested_region} currently has "
                f"{len(recommendations)} relevant growth "
                "opportunity"
            )

        else:

            opening = (
                f"{requested_region} currently has "
                f"{len(recommendations)} decision-relevant "
                "priority issue"
            )

        if (
            len(recommendations)
            !=
            1
        ):

            opening += "s"

        opening += "."

    else:

        unique_regions = {
            str(
                item.get(
                    "dimension_value"
                )
            )
            for item
            in recommendations
            if (
                _normalize_text(
                    item.get(
                        "dimension"
                    )
                )
                ==
                "region"
                and
                item.get(
                    "dimension_value"
                )
            )
        }

        if (
            selection_mode
            ==
            "risk_attention"
            and
            unique_regions
        ):

            opening = (
                "The current priority layer identifies "
                f"{len(unique_regions)} risk region"
            )

            if (
                len(unique_regions)
                !=
                1
            ):

                opening += "s"

            opening += (
                " requiring management attention."
            )

        elif (
            selection_mode
            ==
            "growth_opportunity"
            and
            unique_regions
        ):

            opening = (
                "The current priority layer identifies "
                f"{len(unique_regions)} region"
            )

            if (
                len(unique_regions)
                !=
                1
            ):

                opening += "s"

            opening += (
                " with active growth opportunities."
            )

        else:

            opening = (
                "The current priority layer contains "
                "the following decision-relevant priorities."
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

        focus = (
            recommendation[
                "management_focus"
            ]
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
            if evidence_items
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
            if actions
            else
            focus
        )

        sections.append(
            (
                f"{index}. {scope} "
                f"({severity}{score_text}): "
                f"{focus} "
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
# PUBLIC RECOMMENDATION ENGINE
# ============================================================

def build_recommendation_response(
    question: str,
    limit: int = 4,
) -> dict:

    started_at = (
        perf_counter()
    )

    safe_limit = max(
        1,
        min(
            int(limit),
            10,
        ),
    )

    insights = (
        load_active_insights(
            limit=100
        )
    )

    (
        selected,
        requested_region,
        selection_mode,
    ) = (
        _select_insights(
            insights,
            question,
            safe_limit,
        )
    )

    recommendations = [
        _build_recommendation(
            insight
        )
        for insight
        in selected
    ]

    period = (
        _month_context()
    )

    metric_hint = (
        _metric_hint(
            question
        )
    )

    response_time_ms = round(
        (
            perf_counter()
            -
            started_at
        )
        *
        1000,
        2,
    )

    warnings: list[str] = []

    if not recommendations:

        warnings.append(
            (
                "No active persisted insights matched "
                "the recommendation request."
            )
        )

    return {
        "status":
            "success",

        "question":
            question.strip(),

        "answer":
            _compose_answer(
                recommendations,
                requested_region,
                selection_mode,
            ),

        "intent": {
            "analysis_type":
                "recommendations",

            "metric":
                metric_hint,

            "dimension":
                (
                    "region"
                    if (
                        requested_region
                        or
                        "region"
                        in _normalize_text(
                            question
                        )
                    )
                    else
                    "overall"
                ),

            "dimension_value":
                requested_region,

            "current_start":
                period[
                    "current_start"
                ],

            "current_end":
                period[
                    "current_end"
                ],

            "comparison_start":
                period[
                    "comparison_start"
                ],

            "comparison_end":
                period[
                    "comparison_end"
                ],

            "target_month":
                None,

            "promotion_start":
                None,

            "promotion_end":
                None,

            "confidence":
                0.95,
        },

        "parser":
            "deterministic_recommendation",

        "tool_used":
            "recommend_business_actions",

        "used_llm":
            False,

        "llm_usage": {
            "intent":
                False,

            "response":
                False,
        },

        "execution_mode":
            "fast_path",

        "response_time_ms":
            response_time_ms,

        "evidence": {
            "source":
                "analytics.business_insights",

            "selection_mode":
                selection_mode,

            "requested_region":
                requested_region,

            "question_focus":
                _question_focus(
                    question
                ),

            "active_insights_scanned":
                len(
                    insights
                ),

            "recommendation_count":
                len(
                    recommendations
                ),

            "recommendations":
                _json_safe(
                    recommendations
                ),
        },

        "warnings":
            warnings,

        "analysis_id":
            str(
                uuid4()
            ),
    }