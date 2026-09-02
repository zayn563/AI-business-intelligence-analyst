import {
    NextResponse,
} from "next/server";


const FASTAPI_BASE_URL =
    process.env.FASTAPI_BASE_URL
    ??
    "http://127.0.0.1:8000";


export async function POST() {

    try {

        const response =
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
                status:
                    "failed",

                detail:
                    "Decision intelligence service could not be reached.",
            },
            {
                status:
                    500,
            },
        );
    }
}