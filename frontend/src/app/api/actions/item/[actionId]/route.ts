import {
    NextRequest,
    NextResponse,
} from "next/server";


const FASTAPI_BASE_URL =
    process.env.FASTAPI_BASE_URL
    ??
    "http://127.0.0.1:8000";


export async function PATCH(
    request:
        NextRequest,

    {
        params,
    }: {
        params:
            Promise<{
                actionId:
                    string;
            }>;
    },
) {

    const {
        actionId,
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
                    `/intelligence/actions/`
                    +
                    `${actionId}`
                ),
                {
                    method:
                        "PATCH",

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
                    "Action could not be updated.",
            },
            {
                status:
                    500,
            },
        );
    }
}


export async function DELETE(
    _request:
        NextRequest,

    {
        params,
    }: {
        params:
            Promise<{
                actionId:
                    string;
            }>;
    },
) {

    const {
        actionId,
    } =
        await params;


    try {

        const response =
            await fetch(
                (
                    `${FASTAPI_BASE_URL}`
                    +
                    `/intelligence/actions/`
                    +
                    `${actionId}`
                ),
                {
                    method:
                        "DELETE",

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
                    "Action could not be deleted.",
            },
            {
                status:
                    500,
            },
        );
    }
}