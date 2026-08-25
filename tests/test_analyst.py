from datetime import date

from backend.app.analyst.intent_parser import (
    normalize_ollama_intent_payload,
    parse_intent,
)

from backend.app.analyst.llm_client import (
    clean_llm_text,
    extract_json_text,
)

from backend.app.analyst.models import (
    AnalystIntent,
)

from backend.app.analyst.response_composer import (
    compose_answer,
)


# ============================================================
# FAST PATH — TARGET
# ============================================================

def test_target_fast_path():

    (
        intent,
        parser,
        warnings,
    ) = (
        parse_intent(
            (
                "How did East perform against "
                "target in July 2026?"
            )
        )
    )

    assert (
        intent.analysis_type
        ==
        "targets"
    )

    assert (
        intent.dimension_value
        ==
        "East"
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
        "deterministic_fast_path"
    )

    assert (
        warnings
        ==
        []
    )


# ============================================================
# FAST PATH — PROMOTION
# ============================================================

def test_promotion_fast_path():

    (
        intent,
        parser,
        warnings,
    ) = (
        parse_intent(
            (
                "Did the April 2026 "
                "promotion work?"
            )
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

    assert (
        parser
        ==
        "deterministic_fast_path"
    )

    assert (
        warnings
        ==
        []
    )


# ============================================================
# FAST PATH — DIAGNOSTIC
# ============================================================

def test_diagnostic_fast_path():

    (
        intent,
        parser,
        warnings,
    ) = (
        parse_intent(
            (
                "Why did North sales decline "
                "in June 2026?"
            )
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

    assert (
        intent.comparison_end
        ==
        date(
            2026,
            5,
            31,
        )
    )

    assert (
        parser
        ==
        "deterministic_fast_path"
    )

    assert (
        warnings
        ==
        []
    )


# ============================================================
# FAST PATH — SOUTH MARGIN
# ============================================================

def test_south_margin_fast_path():

    (
        intent,
        parser,
        _warnings,
    ) = (
        parse_intent(
            (
                "What drove South margin "
                "deterioration in July 2026?"
            )
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
        "margin_pct"
    )

    assert (
        intent.dimension_value
        ==
        "South"
    )

    assert (
        parser
        ==
        "deterministic_fast_path"
    )


# ============================================================
# FAST PATH — EXECUTIVE
# ============================================================

def test_latest_changes_fast_path():

    (
        intent,
        parser,
        warnings,
    ) = (
        parse_intent(
            (
                "What are the most important "
                "business issues I should focus on?"
            )
        )
    )

    assert (
        intent.analysis_type
        ==
        "latest_changes"
    )

    assert (
        parser
        ==
        "deterministic_fast_path"
    )

    assert (
        warnings
        ==
        []
    )


# ============================================================
# FORCED FALLBACK
# ============================================================

def test_force_fallback():

    (
        intent,
        parser,
        warnings,
    ) = (
        parse_intent(
            (
                "Why did North sales decline "
                "in June 2026?"
            ),
            force_fallback=True,
        )
    )

    assert (
        intent.analysis_type
        ==
        "diagnostic"
    )

    assert (
        parser
        ==
        "deterministic_fallback"
    )

    assert (
        warnings
        ==
        []
    )


# ============================================================
# AMBIGUOUS QUESTION
# ============================================================

def test_ambiguous_question_is_not_fast_path():

    (
        intent,
        parser,
        _warnings,
    ) = (
        parse_intent(
            (
                "Something feels off with northern "
                "performance around the beginning "
                "of summer. Can you figure out "
                "what is going on?"
            ),
            force_fallback=True,
        )
    )

    assert (
        intent.analysis_type
        ==
        "unsupported"
    )

    assert (
        parser
        ==
        "deterministic_fallback"
    )


# ============================================================
# OLLAMA ALIAS NORMALIZATION
# ============================================================

def test_ollama_alias_normalization():

    raw_payload = {
        "analysis_type":
            "decline",

        "metric":
            "sales",

        "dimension":
            "region",

        "dimension_value":
            "north",
    }

    normalized = (
        normalize_ollama_intent_payload(
            raw_payload
        )
    )

    assert (
        normalized[
            "analysis_type"
        ]
        ==
        "diagnostic"
    )

    assert (
        normalized[
            "metric"
        ]
        ==
        "net_sales"
    )

    assert (
        normalized[
            "dimension"
        ]
        ==
        "region"
    )

    assert (
        normalized[
            "dimension_value"
        ]
        ==
        "North"
    )


# ============================================================
# THINKING CLEANUP
# ============================================================

def test_clean_llm_text_removes_partial_thinking():

    raw = """
The user asked for a specific response.
I should comply.
</think>

LOCAL AI OK
"""

    cleaned = (
        clean_llm_text(
            raw
        )
    )

    assert (
        cleaned
        ==
        "LOCAL AI OK"
    )


def test_clean_llm_text_removes_standard_thinking():

    raw = """
<think>
Internal reasoning must not reach the user.
</think>

Business response.
"""

    cleaned = (
        clean_llm_text(
            raw
        )
    )

    assert (
        cleaned
        ==
        "Business response."
    )


# ============================================================
# JSON EXTRACTION
# ============================================================

def test_extract_json_text():

    raw = """
Reasoning text.
</think>

{
    "analysis_type": "diagnostic",
    "metric": "net_sales"
}
"""

    extracted = (
        extract_json_text(
            raw
        )
    )

    assert (
        '"analysis_type": "diagnostic"'
        in
        extracted
    )

    assert (
        '"metric": "net_sales"'
        in
        extracted
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
                    -29.90,

                "change_pp":
                    None,

                "diagnostic": {

                    "diagnosis":
                        "volume_and_availability",

                    "drivers": {

                        "units_change_pct":
                            -29.53,

                        "asp_change_pct":
                            -0.53,

                        "cost_per_unit_change_pct":
                            -0.70,

                        "discount_change_pp":
                            -0.04,

                        "stockout_rate_change_pp":
                            12.16,

                        "margin_change_pp":
                            0.10,
                    },
                },
            },
        },
    }

    (
        answer,
        used_llm,
        warnings,
    ) = (
        compose_answer(
            question=
                (
                    "Why did North "
                    "sales decline?"
                ),

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
        "declined 29.90%"
        in
        answer
    )

    assert (
        "declined -29.90%"
        not in
        answer
    )

    assert (
        used_llm
        is False
    )

    assert (
        warnings
        ==
        []
    )


# ============================================================
# DEFAULT RESPONSE DOES NOT REQUIRE LLM
# ============================================================

def test_default_response_is_deterministic():

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
                    -10.0,

                "change_pp":
                    None,

                "diagnostic": {

                    "diagnosis":
                        "volume_decline",

                    "drivers":
                        {},
                },
            },
        },
    }

    (
        answer,
        used_llm,
        _warnings,
    ) = (
        compose_answer(
            question=
                "Why did North sales decline?",

            intent=
                intent,

            result=
                result,
        )
    )

    assert (
        used_llm
        is False
    )

    assert (
        "North"
        in
        answer
    )