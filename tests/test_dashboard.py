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

    assert (
        "data_through"
        in
        payload
    )

    assert (
        "current_period"
        in
        payload
    )

    assert (
        "comparison_period"
        in
        payload
    )

    assert (
        "kpis"
        in
        payload
    )

    assert (
        "brief"
        in
        payload
    )

    assert (
        "priorities"
        in
        payload
    )

    assert (
        "trend"
        in
        payload
    )

    assert (
        "regions"
        in
        payload
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

    assert (
        "risks"
        in
        priorities
    )

    assert (
        "opportunities"
        in
        priorities
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