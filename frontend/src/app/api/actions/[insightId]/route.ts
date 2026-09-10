import {
    NextRequest,
    NextResponse,
} from "next/server";


const FASTAPI_BASE_URL =
    process.env.FASTAPI_BASE_URL
    ??
    "http://127.0.0.1:8000";


export async function GET(
    _request:
        NextRequest,

    {
        params,
    }: {
        params:
            Promise<{
                insightId:
                    string;
            }>;
    },
) {

    const {
        insightId,
    } =
        await params;


    try {

        const response =
            await fetch(
                (
                    `${FASTAPI_BASE_URL}`
                    +
                    `/intelligence/insights/`
                    +
                    `${insightId}`
                    +
                    `/actions`
                ),
                {
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
    catch {

        return NextResponse.json(
            {
                detail:
                    "Action service could not be reached.",
            },
            {
                status:
                    500,
            },
        );
    }
}


export async function POST(
    request:
        NextRequest,

    {
        params,
    }: {
        params:
            Promise<{
                insightId:
                    string;
            }>;
    },
) {

    const {
        insightId,
    } =
        await params;


    try {

        const body =
            await request.json();


        const response =
            await fetch(
                (
                    `${FASTAPI_BASE_URL}`
                    +
                    `/intelligence/insights/`
                    +
                    `${insightId}`
                    +
                    `/actions`
                ),
                {
                    method:
                        "POST",

                    headers: {
                        "Content-Type":
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
    catch {

        return NextResponse.json(
            {
                detail:
                    "Action could not be created.",
            },
            {
                status:
                    500,
            },
        );
    }
}