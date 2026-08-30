from fastapi.testclient import (
    TestClient,
)

from backend.app.main import app

from backend.app.routes.analyst import (
    normalize_execution_metadata,
)


# ============================================================
# CLIENT
# ============================================================

client = TestClient(
    app
)


# ============================================================
# BROAD MANAGEMENT ATTENTION QUESTION
#
# This must:
# - stay deterministic
# - return 200
# - use only risk/attention priorities
# - exclude positive opportunities
# - avoid Windows encoding corruption
# ============================================================

def test_broad_region_recommendation_question():

    response = client.post(
        "/analyst/ask",
        json={
            "question":
                (
                    "How can we improve sales "
                    "in regions which require attention?"
                )
        },
    )

    assert (
        response.status_code
        ==
        200
    )

    result = (
        response.json()
    )

    assert (
        result[
            "status"
        ]
        ==
        "success"
    )

    assert (
        result[
            "parser"
        ]
        ==
        "deterministic_recommendation"
    )

    assert (
        result[
            "execution_mode"
        ]
        ==
        "fast_path"
    )

    assert (
        result[
            "tool_used"
        ]
        ==
        "recommend_business_actions"
    )

    assert (
        result[
            "used_llm"
        ]
        is
        False
    )

    assert (
        result[
            "intent"
        ][
            "analysis_type"
        ]
        ==
        "recommendations"
    )

    assert (
        result[
            "intent"
        ][
            "dimension"
        ]
        ==
        "region"
    )

    assert (
        result[
            "intent"
        ][
            "dimension_value"
        ]
        is
        None
    )

    assert (
        result[
            "evidence"
        ][
            "selection_mode"
        ]
        ==
        "risk_attention"
    )

    recommendations = (
        result[
            "evidence"
        ][
            "recommendations"
        ]
    )

    assert (
        len(
            recommendations
        )
        >=
        1
    )

    for recommendation in (
        recommendations
    ):

        assert (
            str(
                recommendation.get(
                    "insight_type"
                )
                or
                ""
            )
            .lower()
            !=
            "opportunity"
        )

    # Regression for the observed:
    #
    # "South â ..."
    #
    assert (
        "â"
        not in
        result[
            "answer"
        ]
    )


# ============================================================
# SOUTH PROFITABILITY QUESTION
#
# This should not return the unrelated South target miss.
# ============================================================

def test_south_margin_question_is_profitability_focused():

    response = client.post(
        "/analyst/ask",
        json={
            "question":
                (
                    "What should we do about "
                    "South margin deterioration?"
                )
        },
    )

    assert (
        response.status_code
        ==
        200
    )

    result = (
        response.json()
    )

    assert (
        result[
            "status"
        ]
        ==
        "success"
    )

    assert (
        result[
            "intent"
        ][
            "dimension_value"
        ]
        ==
        "South"
    )

    assert (
        result[
            "evidence"
        ][
            "question_focus"
        ]
        ==
        "profitability"
    )

    recommendations = (
        result[
            "evidence"
        ][
            "recommendations"
        ]
    )

    assert (
        len(
            recommendations
        )
        >=
        1
    )

    for recommendation in (
        recommendations
    ):

        assert (
            recommendation[
                "primary_metric"
            ]
            in {
                "gross_profit",
                "margin_pct",
                "discount_pct",
                "cost_per_unit",
            }
        )

        assert (
            recommendation[
                "action_type"
            ]
            ==
            "profitability"
        )

        assert (
            "target shortfall"
            not in
            recommendation[
                "management_focus"
            ]
            .lower()
        )


# ============================================================
# NORTH GROWTH OPPORTUNITY
#
# Regression for the previous incorrect recommendation:
#
# "Recover underlying demand..."
#
# A positive growth opportunity should get a scale/protect
# recommendation, not a decline-recovery recommendation.
# ============================================================

def test_north_growth_opportunity_gets_growth_policy():

    response = client.post(
        "/analyst/ask",
        json={
            "question":
                (
                    "What should we do to scale "
                    "the North growth opportunity?"
                )
        },
    )

    assert (
        response.status_code
        ==
        200
    )

    result = (
        response.json()
    )

    assert (
        result[
            "status"
        ]
        ==
        "success"
    )

    assert (
        result[
            "intent"
        ][
            "dimension_value"
        ]
        ==
        "North"
    )

    assert (
        result[
            "evidence"
        ][
            "selection_mode"
        ]
        ==
        "growth_opportunity"
    )

    recommendations = (
        result[
            "evidence"
        ][
            "recommendations"
        ]
    )

    assert (
        len(
            recommendations
        )
        >=
        1
    )

    first = (
        recommendations[0]
    )

    assert (
        str(
            first[
                "insight_type"
            ]
        )
        .lower()
        ==
        "opportunity"
    )

    assert (
        first[
            "action_type"
        ]
        ==
        "growth"
    )

    assert (
        "scale"
        in
        first[
            "management_focus"
        ]
        .lower()
    )

    assert (
        "recover underlying demand"
        not in
        first[
            "management_focus"
        ]
        .lower()
    )


# ============================================================
# RECOMMENDATIONS ENDPOINT
# ============================================================

def test_recommendations_endpoint():

    response = client.get(
        "/analyst/recommendations"
    )

    assert (
        response.status_code
        ==
        200
    )

    result = (
        response.json()
    )

    assert (
        result[
            "status"
        ]
        ==
        "success"
    )

    assert (
        result[
            "tool_used"
        ]
        ==
        "recommend_business_actions"
    )

    assert (
        result[
            "evidence"
        ][
            "selection_mode"
        ]
        ==
        "risk_attention"
    )

    assert (
        "recommendations"
        in
        result[
            "evidence"
        ]
    )


# ============================================================
# SPECIFIC REGION ENDPOINT
# ============================================================

def test_recommendations_endpoint_with_region():

    response = client.get(
        "/analyst/recommendations",
        params={
            "region":
                "North",

            "limit":
                3,
        },
    )

    assert (
        response.status_code
        ==
        200
    )

    result = (
        response.json()
    )

    assert (
        result[
            "status"
        ]
        ==
        "success"
    )

    assert (
        result[
            "intent"
        ][
            "dimension_value"
        ]
        ==
        "North"
    )


# ============================================================
# EXISTING DETERMINISTIC DIAGNOSTIC MUST NOT REGRESS
# ============================================================

def test_existing_north_diagnostic_still_works():

    response = client.post(
        "/analyst/ask",
        json={
            "question":
                (
                    "Why did North sales decline "
                    "in June 2026?"
                )
        },
    )

    assert (
        response.status_code
        ==
        200
    )

    result = (
        response.json()
    )

    assert (
        result[
            "status"
        ]
        ==
        "success"
    )

    assert (
        result[
            "parser"
        ]
        ==
        "deterministic_fast_path"
    )

    assert (
        result[
            "tool_used"
        ]
        ==
        "diagnose_business_change"
    )

    assert (
        result[
            "intent"
        ][
            "dimension_value"
        ]
        ==
        "North"
    )

    assert (
        result[
            "used_llm"
        ]
        is
        False
    )

    assert (
        result[
            "execution_mode"
        ]
        ==
        "fast_path"
    )


# ============================================================
# EXECUTION METADATA - OLLAMA
#
# No live Ollama call is needed for this regression test.
# We test the API normalization contract directly.
# ============================================================

def test_ollama_metadata_normalization():

    raw_result = {
        "status":
            "success",

        "parser":
            "ollama_structured",

        "used_llm":
            False,

        "execution_mode":
            "",

        "llm_usage": {
            "intent":
                False,

            "response":
                False,
        },
    }

    result = (
        normalize_execution_metadata(
            raw_result
        )
    )

    assert (
        result[
            "used_llm"
        ]
        is
        True
    )

    assert (
        result[
            "execution_mode"
        ]
        ==
        "local_ai"
    )

    assert (
        result[
            "llm_usage"
        ][
            "intent"
        ]
        is
        True
    )

    assert (
        result[
            "llm_usage"
        ][
            "response"
        ]
        is
        False
    )


# ============================================================
# EXECUTION METADATA - DETERMINISTIC
# ============================================================

def test_fast_path_metadata_normalization():

    raw_result = {
        "status":
            "success",

        "parser":
            "deterministic_fast_path",

        "used_llm":
            False,

        "execution_mode":
            "",
    }

    result = (
        normalize_execution_metadata(
            raw_result
        )
    )

    assert (
        result[
            "used_llm"
        ]
        is
        False
    )

    assert (
        result[
            "execution_mode"
        ]
        ==
        "fast_path"
    )


# ============================================================
# CAPABILITIES
# ============================================================

def test_recommendation_capability_is_exposed():

    response = client.get(
        "/analyst/capabilities"
    )

    assert (
        response.status_code
        ==
        200
    )

    result = (
        response.json()
    )

    assert (
        "recommendations"
        in
        result[
            "supported_analysis"
        ]
    )

    assert (
        result[
            "decision_support"
        ][
            "recommendation_engine"
        ]
        is
        True
    )

    assert (
        result[
            "decision_support"
        ][
            "risk_opportunity_separation"
        ]
        is
        True
    )

    assert (
        result[
            "guardrails"
        ][
            "execution_metadata_normalized"
        ]
        is
        True
    )