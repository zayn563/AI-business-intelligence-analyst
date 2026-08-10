import backend.app.services.orchestration_service as orchestration


# ============================================================
# NO ACTIVE SOURCES
# ============================================================

def test_refresh_with_no_active_sources(
    monkeypatch,
):

    monkeypatch.setattr(
        orchestration,
        "list_sources",
        lambda: [
            {
                "source_id": 1,
                "source_name": "CSV",
                "is_active": False,
            }
        ],
    )

    result = (
        orchestration
        .refresh_active_sources()
    )

    assert (
        result["status"]
        ==
        "no_active_sources"
    )

    assert (
        result[
            "sources_attempted"
        ]
        ==
        0
    )


# ============================================================
# SUCCESSFUL ACTIVE SOURCE
# ============================================================

def test_refresh_active_source_success(
    monkeypatch,
):

    monkeypatch.setattr(
        orchestration,
        "list_sources",
        lambda: [
            {
                "source_id": 2,
                "source_name":
                    "Google Sales",

                "source_type":
                    "google_sheets",

                "is_active":
                    True,
            }
        ],
    )

    monkeypatch.setattr(
        orchestration,
        "refresh_source",
        lambda source_id: {
            "refresh_id":
                100,

            "source_id":
                source_id,

            "source_name":
                "Google Sales",

            "status":
                "success",

            "rows_read":
                100,

            "rows_inserted":
                5,

            "rows_updated":
                2,

            "rows_unchanged":
                93,

            "rows_rejected":
                0,
        },
    )

    result = (
        orchestration
        .refresh_active_sources()
    )

    assert (
        result["status"]
        ==
        "success"
    )

    assert (
        result[
            "sources_succeeded"
        ]
        ==
        1
    )

    assert (
        result[
            "rows_read"
        ]
        ==
        100
    )

    assert (
        result[
            "rows_inserted"
        ]
        ==
        5
    )

    assert (
        result[
            "rows_updated"
        ]
        ==
        2
    )


# ============================================================
# PARTIAL SUCCESS
# ============================================================

def test_refresh_partial_success(
    monkeypatch,
):

    monkeypatch.setattr(
        orchestration,
        "list_sources",
        lambda: [
            {
                "source_id": 2,
                "source_name": "Sales",
                "is_active": True,
            },
            {
                "source_id": 3,
                "source_name": "Inventory",
                "is_active": True,
            },
        ],
    )

    def fake_refresh(
        source_id,
    ):

        if source_id == 3:

            raise ValueError(
                "Inventory source failed"
            )

        return {
            "source_id":
                2,

            "source_name":
                "Sales",

            "status":
                "success",

            "rows_read":
                100,

            "rows_inserted":
                0,

            "rows_updated":
                1,

            "rows_unchanged":
                99,

            "rows_rejected":
                0,
        }

    monkeypatch.setattr(
        orchestration,
        "refresh_source",
        fake_refresh,
    )

    result = (
        orchestration
        .refresh_active_sources()
    )

    assert (
        result["status"]
        ==
        "partial_success"
    )

    assert (
        result[
            "sources_succeeded"
        ]
        ==
        1
    )

    assert (
        result[
            "sources_failed"
        ]
        ==
        1
    )


# ============================================================
# PIPELINE STATUS
# ============================================================

def test_pipeline_status_healthy(
    monkeypatch,
):

    monkeypatch.setattr(
        orchestration,
        "list_sources",
        lambda: [
            {
                "source_id": 1,
                "is_active": False,
                "last_refresh_status":
                    "success",
            },
            {
                "source_id": 2,
                "is_active": True,
                "last_refresh_status":
                    "success",
            },
        ],
    )

    result = (
        orchestration
        .get_pipeline_status()
    )

    assert (
        result["status"]
        ==
        "healthy"
    )

    assert (
        result[
            "active_sources"
        ]
        ==
        1
    )

    assert (
        result[
            "healthy_sources"
        ]
        ==
        1
    )