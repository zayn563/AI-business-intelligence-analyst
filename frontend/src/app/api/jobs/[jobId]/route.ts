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
// GET JOB
// ============================================================

export async function GET(
    _request:
        NextRequest,

    {
        params,
    }: {
        params:
            Promise<{
                jobId:
                    string;
            }>;
    },
) {

    const {
        jobId,
    } =
        await params;


    if (
        !/^\d+$/.test(
            jobId,
        )
    ) {

        return NextResponse.json(
            {
                detail:
                    "Invalid job identifier.",
            },
            {
                status:
                    400,
            },
        );
    }


    try {

        const response =
            await fetch(
                (
                    `${FASTAPI_BASE_URL}`
                    +
                    `/intelligence/jobs/${jobId}`
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
                detail:
                    "Job status could not be loaded.",

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