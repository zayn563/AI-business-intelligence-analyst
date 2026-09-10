from __future__ import annotations


# ============================================================
# RECOMMENDATION
# ============================================================

def recommendation_actions(
    diagnosis: str | None,
    entity: str,
) -> list[dict]:

    diagnosis = (
        diagnosis
        or
        ""
    )


    # --------------------------------------------------------
    # DISCOUNT + COST
    # --------------------------------------------------------

    if diagnosis in {
        "discount_and_cost_pressure",
        "discount_pressure",
        "cost_pressure",
    }:

        return [
            {
                "priority":
                    "HIGH",

                "title":
                    "Review discount depth",

                "reason":
                    (
                        "Margin pressure is associated with "
                        "higher discount intensity."
                    ),
            },

            {
                "priority":
                    "HIGH",

                "title":
                    "Investigate unit-cost inflation",

                "reason":
                    (
                        "Higher cost per unit is reducing "
                        "gross profit and margin."
                    ),
            },

            {
                "priority":
                    "MEDIUM",

                "title":
                    "Identify the worst affected products",

                "reason":
                    (
                        f"Use product contribution within "
                        f"{entity} to focus corrective action."
                    ),
            },
        ]


    # --------------------------------------------------------
    # AVAILABILITY
    # --------------------------------------------------------

    if diagnosis in {
        "volume_and_availability",
        "availability_related_volume_pressure",
        "availability_deterioration",
    }:

        return [
            {
                "priority":
                    "HIGH",

                "title":
                    "Prioritize availability recovery",

                "reason":
                    (
                        "Stockout deterioration is occurring "
                        "alongside weaker unit volume."
                    ),
            },

            {
                "priority":
                    "HIGH",

                "title":
                    "Identify high-stockout products and stores",

                "reason":
                    (
                        "Recovery should focus first on the "
                        "locations with the largest availability "
                        "and volume losses."
                    ),
            },

            {
                "priority":
                    "MEDIUM",

                "title":
                    "Review replenishment cadence",

                "reason":
                    (
                        "Validate whether replenishment timing "
                        "or inventory levels are contributing "
                        "to lost sales."
                    ),
            },
        ]


    # --------------------------------------------------------
    # PRICE-LED GROWTH
    # --------------------------------------------------------

    if diagnosis in {
        "price_led_growth",
        "pricing_change",
    }:

        return [
            {
                "priority":
                    "MEDIUM",

                "title":
                    "Validate price sustainability",

                "reason":
                    (
                        "Confirm that the observed growth can "
                        "continue without materially damaging "
                        "volume."
                    ),
            },

            {
                "priority":
                    "MEDIUM",

                "title":
                    "Identify similar pricing opportunities",

                "reason":
                    (
                        "Look for comparable products or markets "
                        "where price realization may be improved."
                    ),
            },

            {
                "priority":
                    "LOW",

                "title":
                    "Monitor volume response",

                "reason":
                    (
                        "Track whether higher pricing begins to "
                        "reduce units over subsequent periods."
                    ),
            },
        ]


    # --------------------------------------------------------
    # VOLUME-LED GROWTH
    # --------------------------------------------------------

    if diagnosis == "volume_led_growth":

        return [
            {
                "priority":
                    "MEDIUM",

                "title":
                    "Identify the source of incremental volume",

                "reason":
                    (
                        "Determine which products, channels and "
                        "locations are driving growth."
                    ),
            },

            {
                "priority":
                    "MEDIUM",

                "title":
                    "Assess replication potential",

                "reason":
                    (
                        "Identify similar markets where the "
                        "successful pattern can be repeated."
                    ),
            },

            {
                "priority":
                    "LOW",

                "title":
                    "Protect availability",

                "reason":
                    (
                        "Ensure inventory keeps pace with higher "
                        "demand."
                    ),
            },
        ]


    # --------------------------------------------------------
    # TARGET MISS
    # --------------------------------------------------------

    if diagnosis == "target_underperformance":

        return [
            {
                "priority":
                    "HIGH",

                "title":
                    "Identify the largest target gaps",

                "reason":
                    (
                        "Focus recovery activity on products, "
                        "channels and locations contributing the "
                        "largest absolute shortfalls."
                    ),
            },

            {
                "priority":
                    "HIGH",

                "title":
                    "Prioritize recoverable opportunities",

                "reason":
                    (
                        "Separate structural underperformance "
                        "from gaps that can realistically be "
                        "recovered within the period."
                    ),
            },

            {
                "priority":
                    "MEDIUM",

                "title":
                    "Track recovery against target",

                "reason":
                    (
                        "Monitor whether corrective actions are "
                        "closing the remaining gap."
                    ),
            },
        ]


    # --------------------------------------------------------
    # GENERIC
    # --------------------------------------------------------

    return [
        {
            "priority":
                "HIGH",

            "title":
                "Identify the strongest contributors",

            "reason":
                (
                    "Break the issue down by product, channel "
                    "and location before taking corrective action."
                ),
        },

        {
            "priority":
                "MEDIUM",

            "title":
                "Validate the likely driver",

            "reason":
                (
                    "Use supporting KPI movements to distinguish "
                    "correlation from a plausible business driver."
                ),
        },

        {
            "priority":
                "MEDIUM",

            "title":
                "Monitor the next refresh",

            "reason":
                (
                    "Confirm whether the issue persists, improves "
                    "or escalates."
                ),
        },
    ]