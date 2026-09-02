import {
    NextRequest,
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


// ============================================================
// TYPES
// ============================================================

type UnknownRecord =
    Record<
        string,
        unknown
    >;


// ============================================================
// RECORD GUARD
// ============================================================

function isRecord(
    value:
        unknown,
): value is UnknownRecord {

    return (
        typeof value
        ===
        "object"
        &&
        value
        !==
        null
        &&
        !Array.isArray(
            value,
        )
    );
}


// ============================================================
// LATEST QUESTION
//
// This is currently a single-question analyst workspace,
// not a conversational chat.
//
// If multiple non-empty lines are present, only the latest
// line is analyzed.
// ============================================================

function extractLatestQuestion(
    value:
        unknown,
): string {

    if (
        typeof value
        !==
        "string"
    ) {

        return "";
    }


    const normalized =
        value
        .replace(
            /\r\n/g,
            "\n",
        )
        .replace(
            /\r/g,
            "\n",
        );


    const lines =
        normalized
        .split(
            "\n",
        )
        .map(
            (
                line,
            ) => {

                return line.trim();

            },
        )
        .filter(
            (
                line,
            ) => {

                return (
                    line.length
                    >
                    0
                );

            },
        );


    if (
        lines.length
        ===
        0
    ) {

        return "";
    }


    return (
        lines[
            lines.length
            -
            1
        ]
        ??
        ""
    );
}


// ============================================================
// SAFE JSON PARSER
// ============================================================

function parseJsonSafely(
    text:
        string,
): unknown {

    const cleanText =
        text.trim();


    if (
        !cleanText
    ) {

        return null;
    }


    try {

        const parsed:
            unknown =
            JSON.parse(
                cleanText,
            );


        return parsed;

    }
    catch {

        return null;
    }
}


// ============================================================
// ANSWER EXTRACTION
// ============================================================

function extractAnswer(
    payload:
        unknown,
): string | null {

    // --------------------------------------------------------
    // PLAIN STRING
    // --------------------------------------------------------

    if (
        typeof payload
        ===
        "string"
    ) {

        const cleanValue =
            payload.trim();


        return (
            cleanValue
            ?
            cleanValue
            :
            null
        );
    }


    // --------------------------------------------------------
    // OBJECT
    // --------------------------------------------------------

    if (
        !isRecord(
            payload,
        )
    ) {

        return null;
    }


    // --------------------------------------------------------
    // DIRECT ANSWER
    // --------------------------------------------------------

    if (
        typeof payload.answer
        ===
        "string"
        &&
        payload.answer.trim()
    ) {

        return payload.answer.trim();
    }


    // --------------------------------------------------------
    // RESULT.ANSWER
    // --------------------------------------------------------

    if (
        isRecord(
            payload.result,
        )
        &&
        typeof payload.result.answer
        ===
        "string"
        &&
        payload.result.answer.trim()
    ) {

        return payload.result.answer.trim();
    }


    // --------------------------------------------------------
    // DATA.ANSWER
    // --------------------------------------------------------

    if (
        isRecord(
            payload.data,
        )
        &&
        typeof payload.data.answer
        ===
        "string"
        &&
        payload.data.answer.trim()
    ) {

        return payload.data.answer.trim();
    }


    return null;
}


// ============================================================
// ERROR EXTRACTION
// ============================================================

function extractErrorMessage(
    payload:
        unknown,
): string | null {

    if (
        typeof payload
        ===
        "string"
        &&
        payload.trim()
    ) {

        return payload.trim();
    }


    if (
        !isRecord(
            payload,
        )
    ) {

        return null;
    }


    if (
        typeof payload.detail
        ===
        "string"
        &&
        payload.detail.trim()
    ) {

        return payload.detail.trim();
    }


    if (
        typeof payload.error
        ===
        "string"
        &&
        payload.error.trim()
    ) {

        return payload.error.trim();
    }


    if (
        typeof payload.message
        ===
        "string"
        &&
        payload.message.trim()
    ) {

        return payload.message.trim();
    }


    return null;
}


// ============================================================
// GUARDED RESPONSE
// ============================================================

function guardedResponse(
    question:
        string,

    answer:
        string,

    warning:
        string,

    upstreamStatus:
        number | null,
) {

    return {
        status:
            "unsupported",

        question:
            question,

        answer:
            answer,

        intent:
            null,

        parser:
            "frontend_response_guard",

        tool_used:
            null,

        used_llm:
            false,

        execution_mode:
            "guarded_fallback",

        response_time_ms:
            0,

        llm_usage: {
            intent:
                false,

            response:
                false,
        },

        evidence:
            [],

        warnings: [
            warning,
        ],

        upstream_status:
            upstreamStatus,
    };
}


// ============================================================
// POST
// ============================================================

export async function POST(
    request:
        NextRequest,
) {

    const startedAt =
        performance.now();


    // ========================================================
    // READ REQUEST
    // ========================================================

    let requestPayload:
        unknown;


    try {

        requestPayload =
            await request.json();

    }
    catch {

        return NextResponse.json(
            guardedResponse(
                "",
                (
                    "Please enter one business question "
                    +
                    "and try again."
                ),
                "The frontend request body was not valid JSON.",
                null,
            ),
            {
                status:
                    200,
            },
        );
    }


    // ========================================================
    // GET QUESTION
    // ========================================================

    let questionValue:
        unknown =
        null;


    if (
        isRecord(
            requestPayload,
        )
    ) {

        questionValue =
            requestPayload.question;
    }


    const latestQuestion =
        extractLatestQuestion(
            questionValue,
        );


    if (
        !latestQuestion
    ) {

        return NextResponse.json(
            guardedResponse(
                "",
                (
                    "Please enter one business question "
                    +
                    "before running the analysis."
                ),
                "No usable analyst question was supplied.",
                null,
            ),
            {
                status:
                    200,
            },
        );
    }


    // ========================================================
    // FASTAPI REQUEST
    // ========================================================

    let backendResponse:
        Response;


    try {

        backendResponse =
            await fetch(
                (
                    `${FASTAPI_BASE_URL}`
                    +
                    "/analyst/ask"
                ),
                {
                    method:
                        "POST",

                    headers: {
                        Accept:
                            "application/json",

                        "Content-Type":
                            "application/json",
                    },

                    body:
                        JSON.stringify(
                            {
                                question:
                                    latestQuestion,
                            },
                        ),

                    cache:
                        "no-store",
                },
            );

    }
    catch (
        error
    ) {

        let technicalMessage =
            "FastAPI could not be reached.";


        if (
            error
            instanceof
            Error
        ) {

            technicalMessage =
                error.message;
        }


        const payload =
            guardedResponse(
                latestQuestion,
                (
                    "The business analyst is temporarily "
                    +
                    "unavailable. Your question was not lost. "
                    +
                    "Please try again once the local analytics "
                    +
                    "service is available."
                ),
                technicalMessage,
                null,
            );


        payload.response_time_ms =
            Number(
                (
                    performance.now()
                    -
                    startedAt
                )
                .toFixed(
                    2,
                ),
            );


        return NextResponse.json(
            payload,
            {
                status:
                    200,
            },
        );
    }


    // ========================================================
    // READ BACKEND RESPONSE
    // ========================================================

    const responseText =
        await backendResponse.text();


    const parsedPayload =
        parseJsonSafely(
            responseText,
        );


    // ========================================================
    // BACKEND RETURNED NON-2XX
    //
    // Important:
    // An analyst interpretation failure is NOT a network
    // gateway failure. Return a controlled analyst envelope
    // instead of 502.
    // ========================================================

    if (
        !backendResponse.ok
    ) {

        const technicalMessage =
            (
                extractErrorMessage(
                    parsedPayload
                    ??
                    responseText,
                )
                ??
                (
                    "FastAPI returned HTTP "
                    +
                    backendResponse.status
                    +
                    "."
                )
            );


        let userAnswer =
            (
                "I could not map that request to a complete "
                +
                "supported analysis. Please ask one specific "
                +
                "question about a business change, performance "
                +
                "driver, target, promotion, region, product "
                +
                "or other monitored business issue."
            );


        if (
            backendResponse.status
            >=
            500
        ) {

            userAnswer =
                (
                    "I could not complete that analysis right "
                    +
                    "now. Please try a more specific business "
                    +
                    "question, such as which region requires "
                    +
                    "attention, why a KPI changed, how a region "
                    +
                    "performed against target, or whether a "
                    +
                    "promotion worked."
                );
        }


        const payload =
            guardedResponse(
                latestQuestion,
                userAnswer,
                technicalMessage,
                backendResponse.status,
            );


        payload.response_time_ms =
            Number(
                (
                    performance.now()
                    -
                    startedAt
                )
                .toFixed(
                    2,
                ),
            );


        return NextResponse.json(
            payload,
            {
                status:
                    200,
            },
        );
    }


    // ========================================================
    // EXTRACT VALID ANSWER
    // ========================================================

    const answer =
        extractAnswer(
            parsedPayload,
        );


    // ========================================================
    // NORMAL STRUCTURED FASTAPI RESPONSE
    // ========================================================

    if (
        isRecord(
            parsedPayload,
        )
        &&
        answer
    ) {

        return NextResponse.json(
            {
                ...parsedPayload,

                question:
                    latestQuestion,

                answer:
                    answer,

                response_time_ms:
                    (
                        typeof parsedPayload.response_time_ms
                        ===
                        "number"
                        ?
                        parsedPayload.response_time_ms
                        :
                        Number(
                            (
                                performance.now()
                                -
                                startedAt
                            )
                            .toFixed(
                                2,
                            ),
                        )
                    ),
            },
            {
                status:
                    200,
            },
        );
    }


    // ========================================================
    // PLAIN STRING BACKEND RESPONSE
    // ========================================================

    if (
        answer
    ) {

        return NextResponse.json(
            {
                status:
                    "success",

                question:
                    latestQuestion,

                answer:
                    answer,

                intent:
                    null,

                parser:
                    "frontend_normalized",

                tool_used:
                    null,

                used_llm:
                    false,

                execution_mode:
                    "normalized",

                response_time_ms:
                    Number(
                        (
                            performance.now()
                            -
                            startedAt
                        )
                        .toFixed(
                            2,
                        ),
                    ),

                llm_usage: {
                    intent:
                        false,

                    response:
                        false,
                },

                evidence:
                    [],

                warnings:
                    [],
            },
            {
                status:
                    200,
            },
        );
    }


    // ========================================================
    // INVALID SUCCESS ENVELOPE
    // ========================================================

    const fallbackPayload =
        guardedResponse(
            latestQuestion,
            (
                "I could not produce a complete business "
                +
                "analysis for that question. Please ask one "
                +
                "specific question about performance changes, "
                +
                "business drivers, targets or promotions."
            ),
            (
                "FastAPI returned HTTP 200 but did not "
                +
                "include a usable analyst answer."
            ),
            backendResponse.status,
        );


    fallbackPayload.response_time_ms =
        Number(
            (
                performance.now()
                -
                startedAt
            )
            .toFixed(
                2,
            ),
        );


    return NextResponse.json(
        fallbackPayload,
        {
            status:
                200,
        },
    );
}