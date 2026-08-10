from backend.app.intelligence.change_detector import (
    build_change_event,
)

from backend.app.intelligence.driver_analysis import (
    diagnose_change,
)


# ============================================================
# HIGH SALES DECLINE
# ============================================================

def test_high_sales_decline():

    event = (
        build_change_event(
            metric="net_sales",
            dimension="region",
            dimension_value="North",
            current_value=70,
            previous_value=100,
        )
    )

    assert (
        event[
            "change_pct"
        ]
        ==
        -30.0
    )

    assert (
        event[
            "severity"
        ]
        ==
        "high"
    )

    assert (
        event[
            "impact"
        ]
        ==
        "negative"
    )


# ============================================================
# MARGIN PP CHANGE
# ============================================================

def test_margin_uses_percentage_points():

    event = (
        build_change_event(
            metric="margin_pct",
            dimension="region",
            dimension_value="South",
            current_value=30,
            previous_value=34,
        )
    )

    assert (
        event[
            "change_pp"
        ]
        ==
        -4.0
    )

    assert (
        event[
            "severity"
        ]
        ==
        "high"
    )


# ============================================================
# VOLUME + AVAILABILITY
# ============================================================

def test_volume_and_availability_diagnosis():

    event = (
        build_change_event(
            metric="net_sales",
            dimension="region",
            dimension_value="North",
            current_value=70,
            previous_value=100,
        )
    )

    current = {
        "units_sold": 70,
        "avg_selling_price": 2.90,
        "cost_per_unit": 1.50,
        "discount_pct": 2,
        "stockout_rate": 12,
        "margin_pct": 35,
    }

    previous = {
        "units_sold": 100,
        "avg_selling_price": 2.91,
        "cost_per_unit": 1.50,
        "discount_pct": 2,
        "stockout_rate": 2,
        "margin_pct": 35,
    }

    diagnosis = (
        diagnose_change(
            event,
            current,
            previous,
        )
    )

    assert (
        diagnosis[
            "diagnosis"
        ]
        ==
        "volume_and_availability"
    )

    assert (
        diagnosis[
            "confidence"
        ]
        ==
        "high"
    )


# ============================================================
# PRICE-LED GROWTH
# ============================================================

def test_price_led_growth():

    event = (
        build_change_event(
            metric="net_sales",
            dimension="product",
            dimension_value="10 | Product",
            current_value=111,
            previous_value=100,
        )
    )

    current = {
        "units_sold": 100,
        "avg_selling_price": 3.33,
        "cost_per_unit": 2.00,
        "discount_pct": 1,
        "stockout_rate": 2,
        "margin_pct": 35,
    }

    previous = {
        "units_sold": 100,
        "avg_selling_price": 3.00,
        "cost_per_unit": 2.00,
        "discount_pct": 1,
        "stockout_rate": 2,
        "margin_pct": 35,
    }

    diagnosis = (
        diagnose_change(
            event,
            current,
            previous,
        )
    )

    assert (
        diagnosis[
            "diagnosis"
        ]
        ==
        "price_led_growth"
    )


# ============================================================
# DISCOUNT + COST PRESSURE
# ============================================================

def test_discount_and_cost_pressure():

    event = (
        build_change_event(
            metric="margin_pct",
            dimension="region",
            dimension_value="South",
            current_value=27,
            previous_value=34,
        )
    )

    current = {
        "units_sold": 100,
        "avg_selling_price": 3,
        "cost_per_unit": 2.20,
        "discount_pct": 10,
        "stockout_rate": 2,
        "margin_pct": 27,
    }

    previous = {
        "units_sold": 100,
        "avg_selling_price": 3,
        "cost_per_unit": 2.00,
        "discount_pct": 2,
        "stockout_rate": 2,
        "margin_pct": 34,
    }

    diagnosis = (
        diagnose_change(
            event,
            current,
            previous,
        )
    )

    assert (
        diagnosis[
            "diagnosis"
        ]
        ==
        "discount_and_cost_pressure"
    )