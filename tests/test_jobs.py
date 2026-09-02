from uuid import uuid4

from backend.app.jobs.job_store import (
    create_job,
    delete_job,
    get_job,
    get_job_events,
    mark_job_completed,
    mark_job_running,
    update_job_stage,
)


def test_job_store_lifecycle():

    requested_by = (
        "pytest-"
        +
        uuid4().hex[
            :8
        ]
    )


    job = create_job(
        job_type=
            "ANALYZE_ONLY",
        requested_by=
            requested_by,
    )


    job_id = (
        job[
            "job_id"
        ]
    )


    try:

        assert (
            job[
                "status"
            ]
            ==
            "QUEUED"
        )


        mark_job_running(
            job_id,
            stage=
                "ANALYZING",
            progress_pct=
                25,
            message=
                "Running test analysis.",
        )


        running = (
            get_job(
                job_id
            )
        )


        assert running is not None

        assert (
            running[
                "status"
            ]
            ==
            "RUNNING"
        )

        assert (
            running[
                "stage"
            ]
            ==
            "ANALYZING"
        )


        update_job_stage(
            job_id,
            stage=
                "ANALYZING",
            progress_pct=
                75,
            message=
                "Finishing test analysis.",
        )


        mark_job_completed(
            job_id,
            result={
                "test":
                    True,
            },
            message=
                "Test completed.",
        )


        completed = (
            get_job(
                job_id
            )
        )


        assert completed is not None

        assert (
            completed[
                "status"
            ]
            ==
            "COMPLETED"
        )

        assert (
            completed[
                "progress_pct"
            ]
            ==
            100
        )


        events = (
            get_job_events(
                job_id
            )
        )


        assert (
            len(
                events
            )
            >=
            4
        )


        assert (
            events[
                0
            ][
                "event_type"
            ]
            ==
            "JOB_QUEUED"
        )


    finally:

        delete_job(
            job_id
        )