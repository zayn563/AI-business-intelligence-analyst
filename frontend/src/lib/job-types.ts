// ============================================================
// BACKGROUND INTELLIGENCE JOB TYPES
// ============================================================


export type IntelligenceJobType =
    "ANALYZE_ONLY"
    |
    "REFRESH_AND_ANALYZE";


export type IntelligenceJobStatus =
    "QUEUED"
    |
    "RUNNING"
    |
    "COMPLETED"
    |
    "FAILED";


export type IntelligenceJobStage =
    "QUEUED"
    |
    "REFRESHING"
    |
    "ANALYZING"
    |
    "COMPLETED"
    |
    "FAILED";


// ============================================================
// JOB
// ============================================================

export type IntelligenceJob = {

    job_id:
        number;

    job_type:
        IntelligenceJobType;

    status:
        IntelligenceJobStatus;

    stage:
        IntelligenceJobStage;

    progress_pct:
        number;

    requested_by:
        string;

    message:
        string | null;

    result:
        Record<
            string,
            unknown
        >
        |
        null;

    error_detail:
        string | null;

    created_at:
        string;

    started_at:
        string | null;

    completed_at:
        string | null;
};


// ============================================================
// JOB CREATE RESPONSE
// ============================================================

export type IntelligenceJobCreateResponse = {

    created:
        boolean;

    reused:
        boolean;

    job:
        IntelligenceJob;
};


// ============================================================
// JOB EVENT
// ============================================================

export type IntelligenceJobEvent = {

    event_id:
        number;

    job_id:
        number;

    event_type:
        string;

    stage:
        string;

    message:
        string;

    payload:
        Record<
            string,
            unknown
        >
        |
        null;

    created_at:
        string;
};


// ============================================================
// EVENT RESPONSE
// ============================================================

export type IntelligenceJobEventsResponse = {

    job_id:
        number;

    count:
        number;

    results:
        IntelligenceJobEvent[];
};


// ============================================================
// LATEST JOB RESPONSE
// ============================================================

export type LatestIntelligenceJobResponse = {

    job:
        IntelligenceJob | null;

    detail?:
        string;
};