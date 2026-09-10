import {
    NextRequest,
    NextResponse,
} from "next/server";


// ============================================================
// CONFIGURATION
// ============================================================

const FASTAPI_BASE_URL =
    (
        process.env.FASTAPI_BASE_URL
        ??
        "http://127.0.0.1:8000"
    )
    .replace(
        /\/+$/,
        "",
    );


// ============================================================
// POST — CREATE BACKGROUND JOB
// ============================================================

export async function POST(
    request:
        NextRequest,
) {

    try {

        const body =
            await request.json();


        const response =
            await fetch(
                (
                    `${FASTAPI_BASE_URL}`
                    +
                    "/intelligence/jobs"
                ),
                {
                    method:
                        "POST",

                    headers: {
                        "Content-Type":
                            "application/json",

                        Accept:
                            "application/json",
                    },

                    body:
                        JSON.stringify(
                            body,
                        ),

                    cache:
                        "no-store",
                },
            );


        const payload =
            await response.json();


        return NextResponse.json(
            payload,
            {
                status:
                    response.status,
            },
        );

    }
    catch (error) {

        return NextResponse.json(
            {
                detail:
                    (
                        "Background intelligence "
                        +
                        "service could not be reached."
                    ),

                error:
                    (
                        error
                        instanceof
                        Error
                            ?
                            error.message
                            :
                            "Unknown error"
                    ),
            },
            {
                status:
                    500,
            },
        );
    }
}


// ============================================================
// GET — RECENT JOBS
// ============================================================

export async function GET() {

    try {

        const response =
            await fetch(
                (
                    `${FASTAPI_BASE_URL}`
                    +
                    "/intelligence/jobs?limit=20"
                ),
                {
                    cache:
                        "no-store",

                    headers: {
                        Accept:
                            "application/json",
                    },
                },
            );


        const payload =
            await response.json();


        return NextResponse.json(
            payload,
            {
                status:
                    response.status,
            },
        );

    }
    catch (error) {

        return NextResponse.json(
            {
                count:
                    0,

                results:
                    [],

                detail:
                    (
                        "Background job history "
                        +
                        "could not be loaded."
                    ),

                error:
                    (
                        error
                        instanceof
                        Error
                            ?
                            error.message
                            :
                            "Unknown error"
                    ),
            },
            {
                status:
                    500,
            },
        );
    }
}