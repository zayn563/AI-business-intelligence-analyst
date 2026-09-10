from datetime import (
    date,
)

from fastapi.testclient import (
    TestClient,
)

from backend.app.main import (
    app,
)


client = TestClient(
    app
)


# ============================================================
# ENSURE PERSISTED INTELLIGENCE EXISTS
# ============================================================

def prepare_intelligence():

    response = (
        client.post(
            "/intelligence/run"
        )
    )

    assert (
        response.status_code
        ==
        200
    )


# ============================================================
# DASHBOARD CONTRACT
# ============================================================

def test_dashboard_summary():

    prepare_intelligence()

    response = (
        client.get(
            "/intelligence/dashboard-summary"
        )
    )

    assert (
        response.status_code
        ==
        200
    )

    payload = (
        response.json()
    )

    expected = {
        "data_through",
        "current_period",
        "comparison_period",
        "evidence",
        "kpis",
        "brief",
        "priorities",
        "trend",
        "regions",
    }

    assert (
        expected
        .issubset(
            set(
                payload.keys()
            )
        )
    )


# ============================================================
# ANALYTICAL PERIOD CONTRACT
# ============================================================

def test_dashboard_uses_completed_period():

    prepare_intelligence()

    payload = (
        client.get(
            "/intelligence/dashboard-summary"
        )
        .json()
    )

    current_start = (
        date.fromisoformat(
            payload[
                "current_period"
            ][
                "start"
            ]
        )
    )

    current_end = (
        date.fromisoformat(
            payload[
                "current_period"
            ][
                "end"
            ]
        )
    )

    data_through = (
        date.fromisoformat(
            payload[
                "data_through"
            ]
        )
    )

    assert (
        current_start.day
        ==
        1
    )

    assert (
        current_end
        >=
        current_start
    )

    assert (
        current_end
        <=
        data_through
    )


# ============================================================
# KPI CONTRACT
# ============================================================

def test_dashboard_kpis():

    prepare_intelligence()

    response = (
        client.get(
            "/intelligence/dashboard-summary"
        )
    )

    assert (
        response.status_code
        ==
        200
    )

    payload = (
        response.json()
    )

    kpis = (
        payload[
            "kpis"
        ]
    )

    expected = {
        "net_sales",
        "gross_profit",
        "margin_pct",
        "units_sold",
        "target_attainment",
    }

    assert (
        expected
        .issubset(
            set(
                kpis.keys()
            )
        )
    )


# ============================================================
# EVIDENCE CONTRACT
# ============================================================

def test_dashboard_evidence_contract():

    prepare_intelligence()

    payload = (
        client.get(
            "/intelligence/dashboard-summary"
        )
        .json()
    )

    evidence = (
        payload[
            "evidence"
        ]
    )

    expected = {
        "status",
        "reference_data_through",
        "blocking_datasets",
        "mixed_period_warning",
        "blocked_insight_count",
        "blocked_risk_count",
        "blocked_opportunity_count",
    }

    assert (
        expected
        .issubset(
            set(
                evidence.keys()
            )
        )
    )

    assert isinstance(
        evidence[
            "blocking_datasets"
        ],
        list,
    )

    assert (
        evidence[
            "blocked_insight_count"
        ]
        >=
        0
    )


# ============================================================
# PRIORITY CONTRACT
# ============================================================

def test_dashboard_priorities():

    prepare_intelligence()

    response = (
        client.get(
            "/intelligence/dashboard-summary"
        )
    )

    assert (
        response.status_code
        ==
        200
    )

    priorities = (
        response.json()[
            "priorities"
        ]
    )

    expected = {
        "risk_count",
        "active_risk_count",
        "evidence_blocked_risk_count",
        "opportunity_count",
        "active_opportunity_count",
        "evidence_blocked_opportunity_count",
        "risks",
        "opportunities",
    }

    assert (
        expected
        .issubset(
            set(
                priorities.keys()
            )
        )
    )

    assert isinstance(
        priorities[
            "risks"
        ],
        list,
    )

    assert isinstance(
        priorities[
            "opportunities"
        ],
        list,
    )

    assert (
        priorities[
            "risk_count"
        ]
        +
        priorities[
            "evidence_blocked_risk_count"
        ]
        ==
        priorities[
            "active_risk_count"
        ]
    )

    assert (
        priorities[
            "opportunity_count"
        ]
        +
        priorities[
            "evidence_blocked_opportunity_count"
        ]
        ==
        priorities[
            "active_opportunity_count"
        ]
    )


# ============================================================
# OVERVIEW MUST NOT PRESENT BLOCKED PRIOR ISSUES AS CURRENT
# ============================================================

def test_dashboard_current_cards_exclude_resolution_blocked():

    prepare_intelligence()

    priorities = (
        client.get(
            "/intelligence/dashboard-summary"
        )
        .json()[
            "priorities"
        ]
    )

    for insight in (
        priorities[
            "risks"
        ]
        +
        priorities[
            "opportunities"
        ]
    ):

        assert (
            insight.get(
                "resolution_blocked"
            )
            is not
            True
        )


# ============================================================
# BRIEF COUNT CONSISTENCY
# ============================================================

def test_dashboard_brief_counts():

    prepare_intelligence()

    payload = (
        client.get(
            "/intelligence/dashboard-summary"
        )
        .json()
    )

    brief = (
        payload[
            "brief"
        ]
    )

    priorities = (
        payload[
            "priorities"
        ]
    )

    assert (
        brief[
            "current_risk_count"
        ]
        ==
        priorities[
            "risk_count"
        ]
    )

    assert (
        brief[
            "evidence_blocked_risk_count"
        ]
        ==
        priorities[
            "evidence_blocked_risk_count"
        ]
    )

    assert (
        brief[
            "current_opportunity_count"
        ]
        ==
        priorities[
            "opportunity_count"
        ]
    )