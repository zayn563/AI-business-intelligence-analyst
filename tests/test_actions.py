from uuid import uuid4

from fastapi.testclient import (
    TestClient,
)

from backend.app.main import (
    app,
)


client = TestClient(
    app
)


def get_test_insight_id() -> int:

    run_response = (
        client.post(
            "/intelligence/run"
        )
    )

    assert (
        run_response.status_code
        ==
        200
    )

    priorities = (
        client.get(
            "/intelligence/priorities"
        )
        .json()[
            "results"
        ]
    )

    assert priorities

    return int(
        priorities[
            0
        ][
            "insight_id"
        ]
    )


def test_action_lifecycle():

    insight_id = (
        get_test_insight_id()
    )

    title = (
        "Test action "
        +
        uuid4().hex[
            :8
        ]
    )

    create_response = (
        client.post(
            (
                f"/intelligence/insights/"
                f"{insight_id}"
                "/actions"
            ),
            json={
                "title":
                    title,

                "owner":
                    "Portfolio User",

                "notes":
                    "Temporary automated test action.",
            },
        )
    )

    assert (
        create_response.status_code
        ==
        200
    )

    created = (
        create_response.json()
    )

    action_id = int(
        created[
            "action_id"
        ]
    )

    assert (
        created[
            "status"
        ]
        ==
        "OPEN"
    )


    list_response = (
        client.get(
            (
                f"/intelligence/insights/"
                f"{insight_id}"
                "/actions"
            )
        )
    )

    assert (
        list_response.status_code
        ==
        200
    )

    assert any(
        action[
            "action_id"
        ]
        ==
        action_id

        for action
        in list_response.json()[
            "results"
        ]
    )


    update_response = (
        client.patch(
            (
                f"/intelligence/actions/"
                f"{action_id}"
            ),
            json={
                "status":
                    "IN_PROGRESS",
            },
        )
    )

    assert (
        update_response.status_code
        ==
        200
    )

    assert (
        update_response.json()[
            "status"
        ]
        ==
        "IN_PROGRESS"
    )


    completed_response = (
        client.patch(
            (
                f"/intelligence/actions/"
                f"{action_id}"
            ),
            json={
                "status":
                    "COMPLETED",
            },
        )
    )

    assert (
        completed_response.status_code
        ==
        200
    )

    assert (
        completed_response.json()[
            "completed_at"
        ]
        is not None
    )


    delete_response = (
        client.delete(
            (
                f"/intelligence/actions/"
                f"{action_id}"
            )
        )
    )

    assert (
        delete_response.status_code
        ==
        200
    )