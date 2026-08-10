def pct_change(
    current,
    previous,
):

    if (
        current is None
        or
        previous is None
        or
        previous == 0
    ):

        return None

    return (
        (
            current
            -
            previous
        )
        /
        abs(previous)
        *
        100.0
    )


def delta(
    current,
    previous,
):

    if (
        current is None
        or
        previous is None
    ):

        return None

    return (
        current
        -
        previous
    )


def rounded(
    value,
):

    if value is None:

        return None

    return round(
        float(value),
        2,
    )


# ============================================================
# DRIVER ANALYSIS
# ============================================================

def diagnose_change(
    event: dict,
    current_row: dict,
    previous_row: dict,
) -> dict:

    metric = (
        event[
            "metric"
        ]
    )

    units_change = (
        pct_change(
            current_row.get(
                "units_sold"
            ),
            previous_row.get(
                "units_sold"
            ),
        )
    )

    asp_change = (
        pct_change(
            current_row.get(
                "avg_selling_price"
            ),
            previous_row.get(
                "avg_selling_price"
            ),
        )
    )

    cost_change = (
        pct_change(
            current_row.get(
                "cost_per_unit"
            ),
            previous_row.get(
                "cost_per_unit"
            ),
        )
    )

    discount_change_pp = (
        delta(
            current_row.get(
                "discount_pct"
            ),
            previous_row.get(
                "discount_pct"
            ),
        )
    )

    stockout_change_pp = (
        delta(
            current_row.get(
                "stockout_rate"
            ),
            previous_row.get(
                "stockout_rate"
            ),
        )
    )

    margin_change_pp = (
        delta(
            current_row.get(
                "margin_pct"
            ),
            previous_row.get(
                "margin_pct"
            ),
        )
    )


    diagnosis = (
        "mixed_or_unexplained"
    )

    confidence = (
        "medium"
    )


    # ========================================================
    # NET SALES
    # ========================================================

    if metric == "net_sales":

        if (
            event[
                "direction"
            ]
            ==
            "decrease"
        ):

            if (
                units_change
                is not None
                and
                units_change
                <=
                -10
                and
                stockout_change_pp
                is not None
                and
                stockout_change_pp
                >=
                3
            ):

                diagnosis = (
                    "volume_and_availability"
                )

                confidence = (
                    "high"
                )

            elif (
                units_change
                is not None
                and
                units_change
                <=
                -10
            ):

                diagnosis = (
                    "volume_decline"
                )

                confidence = (
                    "high"
                )

            elif (
                asp_change
                is not None
                and
                asp_change
                <=
                -5
            ):

                diagnosis = (
                    "price_decline"
                )

        elif (
            event[
                "direction"
            ]
            ==
            "increase"
        ):

            if (
                units_change
                is not None
                and
                units_change
                >=
                10
                and
                discount_change_pp
                is not None
                and
                discount_change_pp
                >=
                5
            ):

                diagnosis = (
                    "promotion_led_growth"
                )

                confidence = (
                    "high"
                )

            elif (
                asp_change
                is not None
                and
                asp_change
                >=
                5
                and
                (
                    units_change
                    is None
                    or
                    abs(
                        units_change
                    )
                    <=
                    10
                )
            ):

                diagnosis = (
                    "price_led_growth"
                )

                confidence = (
                    "high"
                )

            elif (
                units_change
                is not None
                and
                units_change
                >=
                10
            ):

                diagnosis = (
                    "volume_led_growth"
                )

                confidence = (
                    "high"
                )


    # ========================================================
    # MARGIN
    # ========================================================

    elif metric == "margin_pct":

        if (
            margin_change_pp
            is not None
            and
            margin_change_pp
            < 0
        ):

            if (
                discount_change_pp
                is not None
                and
                discount_change_pp
                >=
                2
                and
                cost_change
                is not None
                and
                cost_change
                >=
                5
            ):

                diagnosis = (
                    "discount_and_cost_pressure"
                )

                confidence = (
                    "high"
                )

            elif (
                cost_change
                is not None
                and
                cost_change
                >=
                5
            ):

                diagnosis = (
                    "cost_pressure"
                )

                confidence = (
                    "high"
                )

            elif (
                discount_change_pp
                is not None
                and
                discount_change_pp
                >=
                2
            ):

                diagnosis = (
                    "discount_pressure"
                )

                confidence = (
                    "high"
                )


    # ========================================================
    # STOCKOUT
    # ========================================================

    elif metric == "stockout_rate":

        if (
            stockout_change_pp
            is not None
            and
            stockout_change_pp
            > 0
        ):

            diagnosis = (
                "availability_deterioration"
            )

            confidence = (
                "high"
            )

        elif (
            stockout_change_pp
            is not None
            and
            stockout_change_pp
            < 0
        ):

            diagnosis = (
                "availability_improvement"
            )

            confidence = (
                "high"
            )


    # ========================================================
    # UNITS
    # ========================================================

    elif metric == "units_sold":

        if (
            units_change
            is not None
            and
            units_change
            < 0
            and
            stockout_change_pp
            is not None
            and
            stockout_change_pp
            >=
            3
        ):

            diagnosis = (
                "availability_related_volume_pressure"
            )

            confidence = (
                "high"
            )


    # ========================================================
    # ASP
    # ========================================================

    elif metric == "avg_selling_price":

        diagnosis = (
            "pricing_change"
        )


    # ========================================================
    # DISCOUNT
    # ========================================================

    elif metric == "discount_pct":

        diagnosis = (
            "promotional_intensity_change"
        )


    return {
        "diagnosis":
            diagnosis,

        "confidence":
            confidence,

        "drivers": {

            "units_change_pct":
                rounded(
                    units_change
                ),

            "asp_change_pct":
                rounded(
                    asp_change
                ),

            "cost_per_unit_change_pct":
                rounded(
                    cost_change
                ),

            "discount_change_pp":
                rounded(
                    discount_change_pp
                ),

            "stockout_rate_change_pp":
                rounded(
                    stockout_change_pp
                ),

            "margin_change_pp":
                rounded(
                    margin_change_pp
                ),
        },
    }