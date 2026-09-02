import {
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
// GET LATEST BACKGROUND JOB
// ============================================================

export async function GET() {

    try {

        const response =
            await fetch(
                (
                    `${FASTAPI_BASE_URL}`
                    +
                    "/intelligence/jobs/latest"
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


        if (
            response.status
            ===
            404
        ) {

            return NextResponse.json(
                {
                    job:
                        null,
                },
                {
                    status:
                        200,
                },
            );
        }


        const payload =
            await response.json();


        if (
            !response.ok
        ) {

            return NextResponse.json(
                {
                    job:
                        null,

                    detail:
                        (
                            payload.detail
                            ??
                            "Latest job could not be loaded."
                        ),
                },
                {
                    status:
                        response.status,
                },
            );
        }


        return NextResponse.json(
            {
                job:
                    payload,
            },
            {
                status:
                    200,
            },
        );

    }
    catch (error) {

        return NextResponse.json(
            {
                job:
                    null,

                detail:
                    (
                        "Latest background job "
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