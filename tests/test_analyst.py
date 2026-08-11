from datetime import date

from backend.app.analyst.intent_parser import (
    parse_intent,
)

from backend.app.analyst.response_composer import (
    compose_answer,
)

from backend.app.analyst.models import (
    AnalystIntent,
)


# ============================================================
# TARGET INTENT
# ============================================================

def test_target_intent_fallback():

    (
        intent,
        parser,
        warnings,
    ) = (
        parse_intent(
            "Which regions missed target in July 2026?",
            force_fallback=True,
        )
    )

    assert (
        intent.analysis_type
        ==
        "targets"
    )

    assert (
        intent.target_month
        ==
        date(
            2026,
            7,
            1,
        )
    )

    assert (
        parser
        ==
        "deterministic_fallback"
    )


# ============================================================
# PROMOTION INTENT
# ============================================================

def test_promotion_intent_fallback():

    (
        intent,
        _parser,
        _warnings,
    ) = (
        parse_intent(
            "Did the April 2026 promotion work?",
            force_fallback=True,
        )
    )

    assert (
        intent.analysis_type
        ==
        "promotions"
    )

    assert (
        intent.promotion_start
        ==
        date(
            2026,
            4,
            1,
        )
    )

    assert (
        intent.promotion_end
        ==
        date(
            2026,
            4,
            30,
        )
    )


# ============================================================
# DIAGNOSTIC INTENT
# ============================================================

def test_diagnostic_intent_fallback():

    (
        intent,
        _parser,
        _warnings,
    ) = (
        parse_intent(
            "Why did North sales decline in June 2026?",
            force_fallback=True,
        )
    )

    assert (
        intent.analysis_type
        ==
        "diagnostic"
    )

    assert (
        intent.metric
        ==
        "net_sales"
    )

    assert (
        intent.dimension
        ==
        "region"
    )

    assert (
        intent.dimension_value
        ==
        "North"
    )

    assert (
        intent.current_start
        ==
        date(
            2026,
            6,
            1,
        )
    )

    assert (
        intent.current_end
        ==
        date(
            2026,
            6,
            30,
        )
    )

    assert (
        intent.comparison_start
        ==
        date(
            2026,
            5,
            1,
        )
    )


# ============================================================
# LATEST CHANGE INTENT
# ============================================================

def test_latest_changes_intent():

    (
        intent,
        _parser,
        _warnings,
    ) = (
        parse_intent(
            "What needs attention in the business?",
            force_fallback=True,
        )
    )

    assert (
        intent.analysis_type
        ==
        "latest_changes"
    )


# ============================================================
# DETERMINISTIC RESPONSE
# ============================================================

def test_deterministic_diagnostic_response():

    intent = AnalystIntent(
        analysis_type=
            "diagnostic",

        metric=
            "net_sales",

        dimension=
            "region",

        dimension_value=
            "North",
    )

    result = {
        "tool":
            "diagnose_business_change",

        "data": {

            "event": {
                "metric":
                    "net_sales",

                "dimension":
                    "region",

                "dimension_value":
                    "North",

                "direction":
                    "decrease",

                "change_pct":
                    -29.9,

                "change_pp":
                    None,

                "diagnostic": {
                    "diagnosis":
                        "volume_and_availability",

                    "drivers": {
                        "units_change_pct":
                            -29.53,

                        "asp_change_pct":
                            -0.3,

                        "stockout_rate_change_pp":
                            12.16,

                        "margin_change_pp":
                            0.1,
                    },
                },
            }
        },
    }

    (
        answer,
        used_llm,
        warnings,
    ) = (
        compose_answer(
            question=
                "Why did North sales decline?",

            intent=
                intent,

            result=
                result,

            force_deterministic=
                True,
        )
    )

    assert (
        "North"
        in
        answer
    )

    assert (
        "29.90%"
        in
        answer
    )

    assert (
        used_llm
        is False
    )