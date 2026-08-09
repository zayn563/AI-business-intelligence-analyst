from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


# ============================================================
# HEALTH
# ============================================================

def test_health():

    response = client.get(
        "/health"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["api"] == "healthy"

    assert (
        data["database"]["database"]
        == "ai_business_intelligence"
    )


# ============================================================
# METADATA
# ============================================================

def test_metadata():

    response = client.get(
        "/metadata"
    )

    assert response.status_code == 200

    data = response.json()

    assert (
        "net_sales"
        in data["supported_metrics"]
    )

    assert (
        "region"
        in data["supported_dimensions"]
    )


# ============================================================
# JULY SUMMARY
# ============================================================

def test_sales_summary():

    payload = {

        "analysis_type":
            "summary",

        "metrics": [
            "net_sales",
            "units_sold"
        ],

        "filters": {},

        "period": {
            "start":
                "2026-07-01",

            "end":
                "2026-07-31"
        }
    }


    response = client.post(
        "/analyze",
        json=payload
    )


    assert response.status_code == 200


    data = response.json()


    assert len(
        data["result"]
    ) == 1


    assert (
        data["result"][0]["net_sales"]
        > 0
    )


    assert (
        data["result"][0]["units_sold"]
        > 0
    )


# ============================================================
# NORTH COMPARISON
# ============================================================

def test_north_june_decline():

    payload = {

        "analysis_type":
            "comparison",

        "metrics": [
            "net_sales",
            "units_sold"
        ],

        "filters": {
            "region":
                "North"
        },

        "period": {
            "start":
                "2026-06-01",

            "end":
                "2026-06-30"
        },

        "comparison_period": {
            "start":
                "2026-05-01",

            "end":
                "2026-05-31"
        }
    }


    response = client.post(
        "/analyze",
        json=payload
    )


    assert response.status_code == 200


    data = response.json()


    assert (
        data["change_pct"]["net_sales"]
        < 0
    )


    assert (
        data["change_pct"]["units_sold"]
        < 0
    )


# ============================================================
# INVALID METRIC MUST BE REJECTED
# ============================================================

def test_invalid_metric_rejected():

    payload = {

        "analysis_type":
            "summary",

        "metrics": [
            "fake_metric"
        ],

        "filters": {},

        "period": {
            "start":
                "2026-07-01",

            "end":
                "2026-07-31"
        }
    }


    response = client.post(
        "/analyze",
        json=payload
    )


    assert response.status_code == 422