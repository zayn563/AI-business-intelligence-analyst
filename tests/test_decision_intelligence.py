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
# RUN DECISION INTELLIGENCE
# ============================================================

def run_cycle() -> dict:

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

    return (
        response.json()
    )


# ============================================================
# PRIORITY SNAPSHOT
# ============================================================

def priority_snapshot() -> dict[
    int,
    tuple[
        str,
        int,
    ],
]:

    response = (
        client.get(
            "/intelligence/priorities"
        )
    )

    assert (
        response.status_code
        ==
        200
    )

    results = (
        response.json()[
            "results"
        ]
    )

    output = {}

    for item in results:

        insight_id = (
            item.get(
                "insight_id"
            )
        )

        if insight_id is None:

            continue

        output[
            int(
                insight_id
            )
        ] = (
            str(
                item.get(
                    "lifecycle_status"
                )
            ),

            int(
                item.get(
                    "occurrence_count"
                )
                or
                0
            ),
        )

    return output


# ============================================================
# RUN ENDPOINT
# ============================================================

def test_decision_intelligence_run():

    payload = (
        run_cycle()
    )

    assert (
        payload[
            "status"
        ]
        ==
        "completed"
    )

    assert (
        "detected"
        in
        payload
    )

    assert (
        "active"
        in
        payload
    )

    assert (
        "brief"
        in
        payload
    )


# ============================================================
# INSIGHTS ARE PERSISTED
# ============================================================

def test_run_persists_insights():

    run_cycle()

    response = (
        client.get(
            "/intelligence/priorities"
        )
    )

    assert (
        response.status_code
        ==
        200
    )

    results = (
        response.json()[
            "results"
        ]
    )

    assert (
        len(
            results
        )
        >
        0
    )

    assert all(
        item.get(
            "insight_id"
        )
        is not None
        for item
        in results
    )


# ============================================================
# SAME PERIOD IS IDEMPOTENT
# ============================================================

def test_same_period_run_is_idempotent():

    run_cycle()

    before = (
        priority_snapshot()
    )

    run_cycle()

    after = (
        priority_snapshot()
    )

    common_ids = (
        set(
            before
        )
        &
        set(
            after
        )
    )

    assert common_ids

    for insight_id in (
        common_ids
    ):

        before_status, before_count = (
            before[
                insight_id
            ]
        )

        after_status, after_count = (
            after[
                insight_id
            ]
        )

        # Re-running the exact same business period should not
        # artificially increase persistence count.
        assert (
            after_count
            ==
            before_count
        )

        # Lifecycle should also remain stable unless analytical
        # evidence actually escalated.
        if (
            before_status
            !=
            "ESCALATED"
        ):

            assert (
                after_status
                in {
                    before_status,
                    "ESCALATED",
                }
            )


# ============================================================
# DASHBOARD GET IS READ ONLY
# ============================================================

def test_dashboard_refresh_does_not_change_lifecycle():

    run_cycle()

    before = (
        priority_snapshot()
    )

    first = (
        client.get(
            "/intelligence/dashboard-summary"
        )
    )

    second = (
        client.get(
            "/intelligence/dashboard-summary"
        )
    )

    assert (
        first.status_code
        ==
        200
    )

    assert (
        second.status_code
        ==
        200
    )

    after = (
        priority_snapshot()
    )

    assert (
        before
        ==
        after
    )


# ============================================================
# PRIORITIES ENDPOINT
# ============================================================

def test_priorities_endpoint():

    run_cycle()

    response = (
        client.get(
            "/intelligence/priorities"
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
        "count"
        in
        payload
    )

    assert (
        "results"
        in
        payload
    )


# ============================================================
# INVESTIGATION ENDPOINT
# ============================================================

def test_investigation_endpoint():

    run_cycle()

    priorities = (
        client.get(
            "/intelligence/priorities"
        )
        .json()[
            "results"
        ]
    )

    risks = [
        item
        for item
        in priorities
        if item.get(
            "type"
        )
        ==
        "risk"
    ]

    assert risks

    insight_id = (
        risks[
            0
        ][
            "insight_id"
        ]
    )

    response = (
        client.get(
            (
                "/intelligence/insights/"
                f"{insight_id}"
                "/investigation"
            )
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
        "insight"
        in
        payload
    )

    assert (
        "breakdowns"
        in
        payload
    )

    assert (
        "recommendations"
        in
        payload
    )


# ============================================================
# SCENARIO ENDPOINT
# ============================================================

def test_scenario_endpoint():

    response = (
        client.post(
            "/intelligence/scenario",
            json={
                "volume_change_pct":
                    5,

                "list_price_change_pct":
                    0,

                "discount_rate_change_pp":
                    -1,

                "cost_per_unit_change_pct":
                    -2,
            },
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
        "baseline"
        in
        payload
    )

    assert (
        "scenario"
        in
        payload
    )

    assert (
        "impact"
        in
        payload
    )