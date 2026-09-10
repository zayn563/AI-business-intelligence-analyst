import {
    NextResponse,
} from "next/server";


// ============================================================
// ROUTE CONFIGURATION
// ============================================================

export const dynamic =
    "force-dynamic";


export const revalidate =
    0;


// ============================================================
// FASTAPI
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


/*
 * This route is used only to determine whether the FastAPI
 * process itself is alive.
 *
 * We intentionally call FastAPI "/" rather than "/health".
 *
 * FastAPI "/health" performs a PostgreSQL connectivity test.
 * That is appropriate for real application health monitoring,
 * but unnecessary for frequent development restart detection.
 */
const FASTAPI_LIVENESS_URL =
    (
        `${FASTAPI_BASE_URL}`
        +
        "/"
    );


// ============================================================
// RESPONSE HEADERS
// ============================================================

const NO_STORE_HEADERS = {

    "Cache-Control":
        "no-store, no-cache, must-revalidate, max-age=0",
};


// ============================================================
// GET
// ============================================================

export async function GET() {

    try {

        const response =
            await fetch(
                FASTAPI_LIVENESS_URL,
                {
                    method:
                        "GET",

                    cache:
                        "no-store",

                    headers: {
                        Accept:
                            "application/json",
                    },

                    /*
                     * This is a localhost process-liveness
                     * request, not a business-data request.
                     */
                    signal:
                        AbortSignal.timeout(
                            1000,
                        ),
                },
            );


        if (
            !response.ok
        ) {

            return NextResponse.json(
                {
                    healthy:
                        false,

                    status:
                        response.status,
                },
                {
                    status:
                        200,

                    headers:
                        NO_STORE_HEADERS,
                },
            );
        }


        return NextResponse.json(
            {
                healthy:
                    true,

                status:
                    response.status,
            },
            {
                status:
                    200,

                headers:
                    NO_STORE_HEADERS,
            },
        );

    }
    catch {

        return NextResponse.json(
            {
                healthy:
                    false,

                status:
                    null,
            },
            {
                status:
                    200,

                headers:
                    NO_STORE_HEADERS,
            },
        );
    }
}