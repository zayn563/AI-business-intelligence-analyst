import {
    NextResponse,
} from "next/server";


const FASTAPI_BASE_URL =
    process.env.FASTAPI_BASE_URL
    ??
    "http://127.0.0.1:8000";


async function safeJson(
    response:
        Response,
):
Promise<Record<string, unknown>> {

    try {

        return (
            await response.json()
        ) as Record<
            string,
            unknown
        >;

    }
    catch {

        return {};
    }
}


export async function POST() {

    try {

        // ----------------------------------------------------
        // REFRESH LIVE SOURCE
        // ----------------------------------------------------

        const refreshResponse =
            await fetch(
                `${FASTAPI_BASE_URL}/pipeline/refresh`,
                {
                    method:
                        "POST",

                    cache:
                        "no-store",

                    headers: {
                        Accept:
                            "application/json",
                    },
                },
            );


        const refresh =
            await safeJson(
                refreshResponse,
            );


        if (
            !refreshResponse.ok
        ) {

            return NextResponse.json(
                {
                    status:
                        "failed",

                    stage:
                        "refresh",

                    refresh,

                    detail:
                        (
                            "Source synchronization failed. "
                            +
                            "Decision intelligence was not rerun."
                        ),
                },
                {
                    status:
                        refreshResponse.status,
                },
            );
        }


        // ----------------------------------------------------
        // RUN INTELLIGENCE ONLY AFTER SUCCESSFUL REFRESH
        // ----------------------------------------------------

        const intelligenceResponse =
            await fetch(
                `${FASTAPI_BASE_URL}/intelligence/run`,
                {
                    method:
                        "POST",

                    cache:
                        "no-store",

                    headers: {
                        Accept:
                            "application/json",
                    },
                },
            );


        const intelligence =
            await safeJson(
                intelligenceResponse,
            );


        if (
            !intelligenceResponse.ok
        ) {

            return NextResponse.json(
                {
                    status:
                        "failed",

                    stage:
                        "intelligence",

                    refresh,

                    intelligence,

                    detail:
                        (
                            "Source synchronization succeeded, "
                            +
                            "but decision intelligence failed."
                        ),
                },
                {
                    status:
                        intelligenceResponse.status,
                },
            );
        }


        return NextResponse.json(
            {
                status:
                    "completed",

                refresh,

                intelligence,
            },
            {
                status:
                    200,
            },
        );

    }
    catch {

        return NextResponse.json(
            {
                status:
                    "failed",

                detail:
                    (
                        "The source refresh workflow "
                        +
                        "could not be completed."
                    ),
            },
            {
                status:
                    500,
            },
        );
    }
}