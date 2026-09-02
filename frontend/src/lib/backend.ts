import type {

    DashboardData,
    DashboardSummary,
    InvestigationResponse,
    PipelineStatusResponse,
    PriorityListResponse,

} from "@/lib/types";


// ============================================================
// BASE URL
// ============================================================

const FASTAPI_BASE_URL =
    process.env.FASTAPI_BASE_URL
    ??
    "http://127.0.0.1:8000";


// ============================================================
// GET
// ============================================================

async function safeGet<T>(
    path: string,
): Promise<T | null> {

    try {

        const response =
            await fetch(
                `${FASTAPI_BASE_URL}${path}`,
                {
                    method:
                        "GET",

                    cache:
                        "no-store",

                    headers: {
                        Accept:
                            "application/json",
                    },
                },
            );


        if (!response.ok) {

            console.error(
                `Backend request failed: ${path}`,
                response.status,
            );

            return null;
        }


        return (
            await response.json()
        ) as T;

    }
    catch (error) {

        console.error(
            `Backend connection failed: ${path}`,
            error,
        );

        return null;
    }
}


// ============================================================
// DASHBOARD
// ============================================================

export async function getDashboardData():
Promise<DashboardData> {

    const summary =
        await safeGet<DashboardSummary>(
            "/intelligence/dashboard-summary",
        );


    return {
        summary,
    };
}


// ============================================================
// PRIORITIES
// ============================================================

export async function getPriorities(
    includeResolved = false,
):
Promise<PriorityListResponse | null> {

    return safeGet<PriorityListResponse>(
        (
            "/intelligence/priorities"
            +
            `?include_resolved=${includeResolved}`
        ),
    );
}


// ============================================================
// INVESTIGATION
// ============================================================

export async function getInvestigation(
    insightId: number,
):
Promise<InvestigationResponse | null> {

    return safeGet<InvestigationResponse>(
        (
            `/intelligence/insights/`
            +
            `${insightId}/investigation`
        ),
    );
}


// ============================================================
// DATA STATUS
// ============================================================

export async function getDataStatus():
Promise<PipelineStatusResponse | null> {

    return safeGet<PipelineStatusResponse>(
        "/pipeline/status",
    );
}