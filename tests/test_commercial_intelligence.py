from backend.app.intelligence.target_analysis import (
    classify_target_achievement,
)

from backend.app.intelligence.promotion_analysis import (
    classify_promotion_performance,
)


def test_target_achieved():

    result = (
        classify_target_achievement(
            103.0
        )
    )

    assert (
        result["status"]
        ==
        "achieved"
    )

    assert (
        result["impact"]
        ==
        "positive"
    )


def test_target_high_priority_miss():

    result = (
        classify_target_achievement(
            86.0
        )
    )

    assert (
        result["status"]
        ==
        "missed"
    )

    assert (
        result["severity"]
        ==
        "high"
    )

    assert (
        result["material"]
        is True
    )


def test_promotion_led_volume_growth():

    result = (
        classify_promotion_performance(
            units_uplift_pct=35,
            revenue_uplift_pct=18,
            discount_change_pp=17,
        )
    )

    assert (
        result["diagnosis"]
        ==
        "promotion_led_volume_growth"
    )

    assert (
        result["effectiveness"]
        ==
        "strong"
    )

    assert (
        result["confidence"]
        ==
        "high"
    )


def test_weak_promotion():

    result = (
        classify_promotion_performance(
            units_uplift_pct=-2,
            revenue_uplift_pct=-5,
            discount_change_pp=10,
        )
    )

    assert (
        result["diagnosis"]
        ==
        "weak_or_negative_response"
    )