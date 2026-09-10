"use client";

import {
    useCallback,
    useEffect,
    useMemo,
    useState,
} from "react";

import {
    useRouter,
} from "next/navigation";

import type {
    IntelligenceJob,
    IntelligenceJobCreateResponse,
    IntelligenceJobEvent,
    IntelligenceJobEventsResponse,
    IntelligenceJobType,
    LatestIntelligenceJobResponse,
} from "@/lib/job-types";

import type {
    PipelineStatusResponse,
} from "@/lib/types";


// ============================================================
// PROPS
// ============================================================

type Props = {

    status:
        PipelineStatusResponse | null;
};


// ============================================================
// DATE FORMATTER
// ============================================================

function formatDateTime(
    value:
        string | null,
): string {

    if (!value) {

        return "—";
    }


    const date =
        new Date(
            value,
        );


    if (
        Number.isNaN(
            date.getTime(),
        )
    ) {

        return value;
    }


    return date.toLocaleString(
        "en-US",
        {
            month:
                "short",

            day:
                "numeric",

            year:
                "numeric",

            hour:
                "numeric",

            minute:
                "2-digit",
        },
    );
}


// ============================================================
// STAGE LABEL
// ============================================================

function stageLabel(
    job:
        IntelligenceJob | null,
): string {

    if (!job) {

        return "No background job has been run yet.";
    }


    switch (
        job.stage
    ) {

        case "QUEUED":

            return "Waiting to start";


        case "REFRESHING":

            return "Synchronizing business data";


        case "ANALYZING":

            return "Running decision intelligence";


        case "COMPLETED":

            return "Workflow completed";


        case "FAILED":

            return "Workflow failed";


        default:

            return job.stage;
    }
}


// ============================================================
// JOB TYPE LABEL
// ============================================================

function jobTypeLabel(
    type:
        IntelligenceJobType,
): string {

    if (
        type
        ===
        "REFRESH_AND_ANALYZE"
    ) {

        return "Data sync + analysis";
    }


    return "Analysis only";
}


// ============================================================
// EVENT LABEL
// ============================================================

function eventLabel(
    event:
        IntelligenceJobEvent,
): string {

    switch (
        event.event_type
    ) {

        case "JOB_QUEUED":

            return "Job queued";


        case "JOB_STAGE":

            if (
                event.stage
                ===
                "REFRESHING"
            ) {

                return "Data synchronization started";
            }


            if (
                event.stage
                ===
                "ANALYZING"
            ) {

                return "Decision intelligence started";
            }


            return "Workflow progressed";


        case "JOB_COMPLETED":

            return "Workflow completed";


        case "JOB_FAILED":

            return "Workflow failed";


        default:

            return event.event_type
                .replaceAll(
                    "_",
                    " ",
                );
    }
}


// ============================================================
// ELAPSED TIME
// ============================================================

function calculateElapsedSeconds(
    job:
        IntelligenceJob | null,

    clockMs:
        number,
): number {

    if (!job) {

        return 0;
    }


    const startedValue =
        job.started_at
        ??
        job.created_at;


    const startMs =
        new Date(
            startedValue,
        )
        .getTime();


    const endMs =
        job.completed_at
            ?
            new Date(
                job.completed_at,
            )
            .getTime()
            :
            clockMs;


    if (
        Number.isNaN(
            startMs,
        )
        ||
        Number.isNaN(
            endMs,
        )
    ) {

        return 0;
    }


    return Math.max(
        0,
        Math.floor(
            (
                endMs
                -
                startMs
            )
            /
            1000,
        ),
    );
}


// ============================================================
// COMPONENT
// ============================================================

export default function DataCenter(
    {
        status,
    }: Props,
) {

    const router =
        useRouter();


    // ========================================================
    // JOB
    // ========================================================

    const [
        job,
        setJob,
    ] =
        useState<
            IntelligenceJob | null
        >(
            null,
        );


    // ========================================================
    // EVENTS
    // ========================================================

    const [
        events,
        setEvents,
    ] =
        useState<
            IntelligenceJobEvent[]
        >(
            [],
        );


    // ========================================================
    // STARTING JOB
    // ========================================================

    const [
        startingJob,
        setStartingJob,
    ] =
        useState<
            IntelligenceJobType | null
        >(
            null,
        );


    // ========================================================
    // CURRENT CLOCK
    // ========================================================

    const [
        clockMs,
        setClockMs,
    ] =
        useState(
            () =>
                Date.now(),
        );


    // ========================================================
    // ERROR
    // ========================================================

    const [
        error,
        setError,
    ] =
        useState<
            string | null
        >(
            null,
        );


    // ========================================================
    // LATEST-JOB LOADING
    // ========================================================

    const [
        loadingLatest,
        setLoadingLatest,
    ] =
        useState(
            true,
        );


    // ========================================================
    // ACTIVE JOB STATE
    // ========================================================

    const jobIsActive =
        useMemo(
            () => {

                return (
                    job
                    !==
                    null
                    &&
                    (
                        job.status
                        ===
                        "QUEUED"
                        ||
                        job.status
                        ===
                        "RUNNING"
                    )
                );

            },
            [
                job,
            ],
        );


    // ========================================================
    // ELAPSED SECONDS
    // ========================================================

    const elapsedSeconds =
        useMemo(
            () => {

                return calculateElapsedSeconds(
                    job,
                    clockMs,
                );

            },
            [
                job,
                clockMs,
            ],
        );


    // ========================================================
    // LOAD EVENTS
    // ========================================================

    const loadEvents =
        useCallback(
            async (
                jobId:
                    number,
            ) => {

                try {

                    const response =
                        await fetch(
                            `/api/jobs/${jobId}/events`,
                            {
                                cache:
                                    "no-store",
                            },
                        );


                    if (
                        !response.ok
                    ) {

                        return;
                    }


                    const payload = (
                        await response.json()
                    ) as IntelligenceJobEventsResponse;


                    setEvents(
                        payload.results
                        ??
                        [],
                    );

                }
                catch {

                    /*
                     * The timeline is supplementary.
                     *
                     * A temporary failure to load events must
                     * not break the main Data workspace.
                     */

                }

            },
            [],
        );


    // ========================================================
    // LOAD JOB
    // ========================================================

    const loadJob =
        useCallback(
            async (
                jobId:
                    number,
            ) => {

                try {

                    const response =
                        await fetch(
                            `/api/jobs/${jobId}`,
                            {
                                cache:
                                    "no-store",
                            },
                        );


                    if (
                        !response.ok
                    ) {

                        return;
                    }


                    const payload = (
                        await response.json()
                    ) as IntelligenceJob;


                    setJob(
                        payload,
                    );


                    await loadEvents(
                        jobId,
                    );


                    if (
                        payload.status
                        ===
                        "COMPLETED"
                        ||
                        payload.status
                        ===
                        "FAILED"
                    ) {

                        router.refresh();
                    }

                }
                catch {

                    /*
                     * Keep displaying the last known job state
                     * if a polling request temporarily fails.
                     */

                }

            },
            [
                loadEvents,
                router,
            ],
        );


    // ========================================================
    // LOAD LATEST JOB
    // ========================================================

    useEffect(
        () => {

            let disposed =
                false;


            async function loadLatestJob() {

                try {

                    const response =
                        await fetch(
                            "/api/jobs/latest",
                            {
                                cache:
                                    "no-store",
                            },
                        );


                    if (
                        !response.ok
                    ) {

                        return;
                    }


                    const payload = (
                        await response.json()
                    ) as LatestIntelligenceJobResponse;


                    if (
                        disposed
                    ) {

                        return;
                    }


                    if (
                        payload.job
                    ) {

                        setJob(
                            payload.job,
                        );


                        await loadEvents(
                            payload
                                .job
                                .job_id,
                        );
                    }

                }
                finally {

                    if (
                        !disposed
                    ) {

                        setLoadingLatest(
                            false,
                        );
                    }
                }
            }


            void loadLatestJob();


            return () => {

                disposed =
                    true;
            };

        },
        [
            loadEvents,
        ],
    );


    // ========================================================
    // POLL ACTIVE JOB
    // ========================================================

    useEffect(
        () => {

            if (
                !job
                ||
                !jobIsActive
            ) {

                return;
            }


            const jobId =
                job.job_id;


            const timer =
                window.setInterval(
                    () => {

                        void loadJob(
                            jobId,
                        );

                    },
                    1500,
                );


            return () => {

                window.clearInterval(
                    timer,
                );
            };

        },
        [
            job,
            jobIsActive,
            loadJob,
        ],
    );


    // ========================================================
    // CLOCK TIMER
    // ========================================================

    useEffect(
        () => {

            if (
                !jobIsActive
            ) {

                return;
            }


            const timer =
                window.setInterval(
                    () => {

                        setClockMs(
                            Date.now(),
                        );

                    },
                    1000,
                );


            return () => {

                window.clearInterval(
                    timer,
                );
            };

        },
        [
            jobIsActive,
        ],
    );


    // ========================================================
    // START JOB
    // ========================================================

    async function startJob(
        jobType:
            IntelligenceJobType,
    ) {

        setStartingJob(
            jobType,
        );


        setError(
            null,
        );


        setEvents(
            [],
        );


        try {

            const response =
                await fetch(
                    "/api/jobs",
                    {
                        method:
                            "POST",

                        headers: {
                            "Content-Type":
                                "application/json",
                        },

                        body:
                            JSON.stringify(
                                {
                                    job_type:
                                        jobType,

                                    requested_by:
                                        "frontend",
                                },
                            ),
                    },
                );


            const payload = (
                await response.json()
            ) as IntelligenceJobCreateResponse
                &
                {
                    detail?:
                        string;
                };


            if (
                !response.ok
            ) {

                setError(
                    payload.detail
                    ??
                    "Background job could not be started.",
                );


                return;
            }


            setJob(
                payload.job,
            );


            setClockMs(
                Date.now(),
            );


            await loadEvents(
                payload
                    .job
                    .job_id,
            );


            window.setTimeout(
                () => {

                    void loadJob(
                        payload
                            .job
                            .job_id,
                    );

                },
                300,
            );

        }
        catch (
            startError
        ) {

            setError(
                (
                    startError
                    instanceof
                    Error
                        ?
                        startError.message
                        :
                        (
                            "The background intelligence "
                            +
                            "service could not be reached."
                        )
                ),
            );

        }
        finally {

            setStartingJob(
                null,
            );
        }
    }


    // ========================================================
    // UI
    // ========================================================

    return (

        <div>

            {/* =================================================
                SOURCE HEALTH
            ================================================= */}

            <div className="data-summary-grid">

                <article>

                    <span>
                        Connected sources
                    </span>


                    <strong>

                        {
                            status
                                ?.active_sources
                            ??
                            0
                        }

                    </strong>

                </article>


                <article>

                    <span>
                        Healthy sources
                    </span>


                    <strong>

                        {
                            status
                                ?.healthy_sources
                            ??
                            0
                        }

                    </strong>

                </article>


                <article>

                    <span>
                        Source status
                    </span>


                    <strong className="data-status-text">

                        {
                            status
                                ?.status
                            ??
                            "Unknown"
                        }

                    </strong>

                </article>

            </div>


            {/* =================================================
                DATA OPERATIONS
            ================================================= */}

            <section className="data-operation-section">

                <div className="section-heading">

                    <div>

                        <span className="section-kicker">

                            DATA OPERATIONS

                        </span>


                        <h2>

                            Update business intelligence

                        </h2>

                    </div>

                </div>


                <div className="data-action-buttons">

                    {/* =========================================
                        ANALYSIS ONLY
                    ========================================= */}

                    <article className="data-action-card quick">

                        <span className="operation-speed">

                            FAST

                        </span>


                        <h3>

                            Analyze current data

                        </h3>


                        <p>

                            Re-run change detection,
                            diagnostics, prioritization and
                            lifecycle management against data
                            already available in PostgreSQL.

                        </p>


                        <button
                            type="button"
                            disabled={
                                jobIsActive
                                ||
                                startingJob
                                !==
                                null
                            }
                            onClick={
                                () =>
                                    void startJob(
                                        "ANALYZE_ONLY",
                                    )
                            }
                        >

                            {
                                startingJob
                                ===
                                "ANALYZE_ONLY"
                                    ?
                                    "Starting..."
                                    :
                                    "Run intelligence now"
                            }

                        </button>

                    </article>


                    {/* =========================================
                        FULL REFRESH
                    ========================================= */}

                    <article className="data-action-card full">

                        <span className="operation-speed">

                            FULL SYNC

                        </span>


                        <h3>

                            Sync source & analyze

                        </h3>


                        <p>

                            Synchronize the connected source,
                            process incremental changes,
                            update PostgreSQL and automatically
                            rerun decision intelligence.

                        </p>


                        <button
                            type="button"
                            disabled={
                                jobIsActive
                                ||
                                startingJob
                                !==
                                null
                            }
                            onClick={
                                () =>
                                    void startJob(
                                        "REFRESH_AND_ANALYZE",
                                    )
                            }
                        >

                            {
                                startingJob
                                ===
                                "REFRESH_AND_ANALYZE"
                                    ?
                                    "Starting..."
                                    :
                                    "Sync latest data & analyze"
                            }

                        </button>

                    </article>

                </div>

            </section>


            {/* =================================================
                BACKGROUND JOB STATUS
            ================================================= */}

            {
                loadingLatest
                    ?
                    (

                        <section className="background-job-panel">

                            <span className="section-kicker">

                                BACKGROUND ACTIVITY

                            </span>


                            <p className="job-message">

                                Loading latest workflow...

                            </p>

                        </section>

                    )
                    :
                    job
                        ?
                        (

                            <section className="background-job-panel">

                                {/* =============================
                                    HEADER
                                ============================= */}

                                <div className="background-job-header">

                                    <div>

                                        <span className="section-kicker">

                                            BACKGROUND ACTIVITY

                                        </span>


                                        <h2>

                                            {
                                                stageLabel(
                                                    job,
                                                )
                                            }

                                        </h2>

                                    </div>


                                    <span
                                        className={
                                            (
                                                "job-status-badge "
                                                +
                                                `job-${job.status.toLowerCase()}`
                                            )
                                        }
                                    >

                                        {
                                            job.status
                                        }

                                    </span>

                                </div>


                                {/* =============================
                                    PROGRESS
                                ============================= */}

                                <div className="job-progress-area">

                                    <div className="job-progress-summary">

                                        <span>

                                            Progress

                                        </span>


                                        <strong>

                                            {
                                                job.progress_pct
                                            }

                                            %

                                        </strong>

                                    </div>


                                    <div className="job-progress-track">

                                        <div
                                            className="job-progress-bar"
                                            style={{
                                                width:
                                                    `${job.progress_pct}%`,
                                            }}
                                        />

                                    </div>

                                </div>


                                {/* =============================
                                    METADATA
                                ============================= */}

                                <div className="job-meta-grid">

                                    <article>

                                        <span>
                                            Job
                                        </span>


                                        <strong>

                                            #
                                            {
                                                job.job_id
                                            }

                                        </strong>

                                    </article>


                                    <article>

                                        <span>

                                            Workflow

                                        </span>


                                        <strong>

                                            {
                                                jobTypeLabel(
                                                    job.job_type,
                                                )
                                            }

                                        </strong>

                                    </article>


                                    <article>

                                        <span>

                                            Elapsed time

                                        </span>


                                        <strong>

                                            {
                                                elapsedSeconds
                                            }

                                            s

                                        </strong>

                                    </article>


                                    <article>

                                        <span>

                                            Started

                                        </span>


                                        <strong>

                                            {
                                                formatDateTime(
                                                    job.started_at
                                                    ??
                                                    job.created_at,
                                                )
                                            }

                                        </strong>

                                    </article>

                                </div>


                                {/* =============================
                                    CURRENT MESSAGE
                                ============================= */}

                                {
                                    job.message
                                    &&
                                    (

                                        <div className="job-current-message">

                                            {
                                                job.message
                                            }

                                        </div>

                                    )
                                }


                                {/* =============================
                                    FAILED JOB
                                ============================= */}

                                {
                                    job.status
                                    ===
                                    "FAILED"
                                    &&
                                    job.error_detail
                                    &&
                                    (

                                        <div className="job-error">

                                            <strong>

                                                Workflow error

                                            </strong>


                                            <p>

                                                {
                                                    job.error_detail
                                                }

                                            </p>

                                        </div>

                                    )
                                }


                                {/* =============================
                                    ACTIVITY TIMELINE
                                ============================= */}

                                {
                                    events.length
                                    >
                                    0
                                    &&
                                    (

                                        <div className="job-timeline">

                                            <div className="job-timeline-heading">

                                                <span className="section-kicker">

                                                    ACTIVITY TIMELINE

                                                </span>


                                                <strong>

                                                    {
                                                        events.length
                                                    }

                                                    {" "}
                                                    events

                                                </strong>

                                            </div>


                                            {
                                                events.map(
                                                    (
                                                        event,
                                                        index,
                                                    ) => (

                                                        <div
                                                            className="job-timeline-row"
                                                            key={
                                                                event.event_id
                                                            }
                                                        >

                                                            <div className="job-timeline-marker">

                                                                <span
                                                                    className={
                                                                        (
                                                                            index
                                                                            ===
                                                                            events.length
                                                                            -
                                                                            1
                                                                                ?
                                                                                (
                                                                                    "timeline-dot "
                                                                                    +
                                                                                    "timeline-dot-current"
                                                                                )
                                                                                :
                                                                                "timeline-dot"
                                                                        )
                                                                    }
                                                                />


                                                                {
                                                                    index
                                                                    <
                                                                    events.length
                                                                    -
                                                                    1
                                                                    &&
                                                                    (

                                                                        <span className="timeline-line" />

                                                                    )
                                                                }

                                                            </div>


                                                            <div className="job-timeline-content">

                                                                <div>

                                                                    <strong>

                                                                        {
                                                                            eventLabel(
                                                                                event,
                                                                            )
                                                                        }

                                                                    </strong>


                                                                    <time>

                                                                        {
                                                                            formatDateTime(
                                                                                event.created_at,
                                                                            )
                                                                        }

                                                                    </time>

                                                                </div>


                                                                <p>

                                                                    {
                                                                        event.message
                                                                    }

                                                                </p>

                                                            </div>

                                                        </div>

                                                    ),
                                                )
                                            }

                                        </div>

                                    )
                                }

                            </section>

                        )
                        :
                        (

                            <section className="background-job-panel">

                                <span className="section-kicker">

                                    BACKGROUND ACTIVITY

                                </span>


                                <h2>

                                    No workflow history yet

                                </h2>


                                <p className="job-message">

                                    Run intelligence or synchronize
                                    the connected data source to
                                    create the first workflow.

                                </p>

                            </section>

                        )
            }


            {/* =================================================
                GENERAL ERROR
            ================================================= */}

            {
                error
                &&
                (

                    <div className="job-error">

                        <strong>

                            Could not start workflow

                        </strong>


                        <p>

                            {
                                error
                            }

                        </p>

                    </div>

                )
            }

        </div>
    );
}