import {
    NextRequest,
    NextResponse,
} from "next/server";


export const dynamic =
    "force-dynamic";

export const revalidate =
    0;

export const runtime =
    "nodejs";


const FASTAPI_BASE_URL =
    (
        process.env.FASTAPI_BASE_URL ??
        "http://127.0.0.1:8000"
    ).replace(
        /\/+$/,
        "",
    );


type JsonRecord =
    Record<string, unknown>;


type ScenarioDimension =
    "overall" |
    "region";


interface ScenarioRequestBody {
    scope?: {
        dimension?: ScenarioDimension;
        value?: string | null;
    };

    volume_change_pct?: number;
    list_price_change_pct?: number;
    discount_rate_change_pp?: number;
    cost_per_unit_change_pct?: number;
}


interface Period {
    start: string;
    end: string;
}


interface ScenarioScope {
    key: string;
    label: string;
    dimension: ScenarioDimension;
    value: string | null;
}


interface MetricCandidate {
    value: number;
    score: number;
}


interface BaselineMetrics {
    net_sales: number;
    gross_profit: number;
    margin_pct: number;
    units_sold: number;
    discount_pct: number;
    cost_per_unit: number;
}


interface ScenarioMetrics
    extends BaselineMetrics {

    gross_sales: number;
    cogs: number;
}


class UpstreamError
    extends Error {

    statusCode: number;

    details: unknown;


    constructor(
        message: string,
        statusCode = 502,
        details: unknown = null,
    ) {

        super(
            message,
        );

        this.name =
            "UpstreamError";

        this.statusCode =
            statusCode;

        this.details =
            details;
    }
}


function isRecord(
    value: unknown,
): value is JsonRecord {

    return (
        typeof value ===
            "object"
        &&
        value !== null
        &&
        !Array.isArray(
            value,
        )
    );
}


function finiteNumber(
    value: unknown,
): number | null {

    if (
        typeof value ===
        "number"
        &&
        Number.isFinite(
            value,
        )
    ) {

        return value;
    }


    if (
        typeof value ===
        "string"
        &&
        value.trim() !==
            ""
    ) {

        const parsed =
            Number(
                value,
            );


        if (
            Number.isFinite(
                parsed,
            )
        ) {

            return parsed;
        }
    }


    return null;
}


function clamp(
    value: number,
    minimum: number,
    maximum: number,
): number {

    return Math.min(
        maximum,
        Math.max(
            minimum,
            value,
        ),
    );
}


function roundMetric(
    value: number,
    decimals = 6,
): number {

    const multiplier =
        10 ** decimals;


    return (
        Math.round(
            (
                value +
                Number.EPSILON
            )
            *
            multiplier,
        )
        /
        multiplier
    );
}


function isoDate(
    value: Date,
): string {

    return value
        .toISOString()
        .slice(
            0,
            10,
        );
}


function parseIsoDate(
    value: string,
): Date {

    const parsed =
        new Date(
            `${value}T00:00:00.000Z`,
        );


    if (
        Number.isNaN(
            parsed.getTime(),
        )
    ) {

        throw new Error(
            (
                "Invalid date returned "
                +
                `by metadata: ${value}`
            ),
        );
    }


    return parsed;
}


function currentMonthPeriod(
    dataThrough: string,
): Period {

    const end =
        parseIsoDate(
            dataThrough,
        );


    const start =
        new Date(
            Date.UTC(
                end.getUTCFullYear(),
                end.getUTCMonth(),
                1,
            ),
        );


    return {
        start:
            isoDate(
                start,
            ),

        end:
            isoDate(
                end,
            ),
    };
}


function previousMonthPeriod(
    currentStart: string,
): Period {

    const start =
        parseIsoDate(
            currentStart,
        );


    const previousStart =
        new Date(
            Date.UTC(
                start.getUTCFullYear(),
                start.getUTCMonth() -
                    1,
                1,
            ),
        );


    const previousEnd =
        new Date(
            Date.UTC(
                start.getUTCFullYear(),
                start.getUTCMonth(),
                0,
            ),
        );


    return {
        start:
            isoDate(
                previousStart,
            ),

        end:
            isoDate(
                previousEnd,
            ),
    };
}


async function parseResponseBody(
    response: Response,
): Promise<unknown> {

    const text =
        await response.text();


    if (
        !text.trim()
    ) {

        return null;
    }


    try {

        return JSON.parse(
            text,
        ) as unknown;

    } catch {

        return text;
    }
}


async function fetchFastApi(
    path: string,
    init?: RequestInit,
): Promise<unknown> {

    let response: Response;


    try {

        response =
            await fetch(
                `${FASTAPI_BASE_URL}${path}`,
                {
                    ...init,

                    headers: {
                        Accept:
                            "application/json",

                        ...(
                            init?.body
                                ? {
                                    "Content-Type":
                                        "application/json",
                                }
                                : {}
                        ),

                        ...init?.headers,
                    },

                    cache:
                        "no-store",
                },
            );

    } catch (error) {

        throw new UpstreamError(
            (
                "FastAPI could not be reached."
            ),
            502,
            error instanceof Error
                ? error.message
                : String(
                    error,
                ),
        );
    }


    const payload =
        await parseResponseBody(
            response,
        );


    if (
        !response.ok
    ) {

        throw new UpstreamError(
            (
                "FastAPI returned an error "
                +
                `for ${path}.`
            ),
            response.status,
            payload,
        );
    }


    return payload;
}


function metadataInfo(
    payload: unknown,
): {
    dataThrough: string;
    regions: string[];
    supportedMetrics: string[];
} {

    if (
        !isRecord(
            payload,
        )
    ) {

        throw new Error(
            "Invalid metadata response.",
        );
    }


    const coverage =
        payload.date_coverage;

    const values =
        payload.available_values;

    const metrics =
        payload.supported_metrics;


    if (
        !isRecord(
            coverage,
        )
        ||
        typeof coverage.end !==
            "string"
    ) {

        throw new Error(
            (
                "Metadata does not contain "
                +
                "date_coverage.end."
            ),
        );
    }


    const regions =
        isRecord(
            values,
        )
        &&
        Array.isArray(
            values.regions,
        )
            ? values.regions
                .filter(
                    (
                        value,
                    ): value is string =>
                        typeof value ===
                        "string",
                )
                .map(
                    (
                        value,
                    ) =>
                        value.trim(),
                )
                .filter(
                    Boolean,
                )
            : [];


    const supportedMetrics =
        Array.isArray(
            metrics,
        )
            ? metrics.filter(
                (
                    value,
                ): value is string =>
                    typeof value ===
                    "string",
            )
            : [];


    return {
        dataThrough:
            coverage.end,

        regions,

        supportedMetrics,
    };
}


function pathPenalty(
    path: string[],
): number {

    const joined =
        path
            .join(
                ".",
            )
            .toLowerCase();


    let penalty =
        0;


    if (
        joined.includes(
            "comparison",
        )
        ||
        joined.includes(
            "previous",
        )
        ||
        joined.includes(
            "prior",
        )
        ||
        joined.includes(
            "baseline_comparison",
        )
    ) {

        penalty +=
            100;
    }


    if (
        joined.includes(
            "current",
        )
        ||
        joined.includes(
            "result",
        )
        ||
        joined.includes(
            "summary",
        )
    ) {

        penalty -=
            10;
    }


    return penalty;
}


function collectMetricCandidates(
    value: unknown,
    metric: string,
    path: string[],
    candidates: MetricCandidate[],
): void {

    if (
        Array.isArray(
            value,
        )
    ) {

        value.forEach(
            (
                item,
                index,
            ) => {

                collectMetricCandidates(
                    item,
                    metric,
                    [
                        ...path,
                        String(
                            index,
                        ),
                    ],
                    candidates,
                );
            },
        );

        return;
    }


    if (
        !isRecord(
            value,
        )
    ) {

        return;
    }


    const penalty =
        pathPenalty(
            path,
        );


    const directMetric =
        finiteNumber(
            value[
                metric
            ],
        );


    if (
        directMetric !==
        null
    ) {

        candidates.push(
            {
                value:
                    directMetric,

                score:
                    120 -
                    penalty,
            },
        );
    }


    const metricName =
        [
            value.metric,
            value.metric_name,
            value.name,
            value.key,
        ]
            .find(
                (
                    candidate,
                ) =>
                    typeof candidate ===
                    "string",
            );


    if (
        typeof metricName ===
            "string"
        &&
        metricName
            .trim()
            .toLowerCase() ===
            metric.toLowerCase()
    ) {

        const prioritizedFields:
            Array<
                [
                    string,
                    number,
                ]
            > = [
                [
                    "current_value",
                    180,
                ],
                [
                    "current",
                    170,
                ],
                [
                    "value",
                    160,
                ],
                [
                    "total",
                    150,
                ],
                [
                    "result",
                    140,
                ],
                [
                    "amount",
                    130,
                ],
            ];


        for (
            const [
                field,
                score,
            ]
            of prioritizedFields
        ) {

            const numeric =
                finiteNumber(
                    value[
                        field
                    ],
                );


            if (
                numeric !==
                null
            ) {

                candidates.push(
                    {
                        value:
                            numeric,

                        score:
                            score -
                            penalty,
                    },
                );
            }
        }
    }


    for (
        const [
            key,
            child,
        ]
        of Object.entries(
            value,
        )
    ) {

        collectMetricCandidates(
            child,
            metric,
            [
                ...path,
                key,
            ],
            candidates,
        );
    }
}


function extractMetric(
    payload: unknown,
    metric: string,
): number {

    const candidates:
        MetricCandidate[] =
        [];


    collectMetricCandidates(
        payload,
        metric,
        [],
        candidates,
    );


    if (
        candidates.length ===
        0
    ) {

        throw new Error(
            (
                "The analytics response did not "
                +
                `contain metric '${metric}'.`
            ),
        );
    }


    candidates.sort(
        (
            left,
            right,
        ) =>
            right.score -
            left.score,
    );


    return candidates[
        0
    ].value;
}


function buildScopes(
    regions: string[],
): ScenarioScope[] {

    return [
        {
            key:
                "overall",

            label:
                "National / Overall",

            dimension:
                "overall",

            value:
                null,
        },

        ...regions.map(
            (
                region,
            ) => (
                {
                    key:
                        (
                            "region:"
                            +
                            region
                        ),

                    label:
                        `${region} region`,

                    dimension:
                        "region" as const,

                    value:
                        region,
                }
            ),
        ),
    ];
}


function canonicalRegion(
    requestedValue: string | null,
    regions: string[],
): string {

    const normalized =
        (
            requestedValue ??
            ""
        )
            .trim()
            .toLowerCase();


    const match =
        regions.find(
            (
                region,
            ) =>
                region
                    .trim()
                    .toLowerCase() ===
                normalized,
        );


    if (
        !match
    ) {

        throw new Error(
            (
                "Unsupported region. "
                +
                `Received '${requestedValue ?? ""}'.`
            ),
        );
    }


    return match;
}


function numericLever(
    value: unknown,
    fallback = 0,
): number {

    const numeric =
        finiteNumber(
            value,
        );


    return (
        numeric ??
        fallback
    );
}


function applyScenario(
    baseline: BaselineMetrics,
    body: ScenarioRequestBody,
): ScenarioMetrics {

    const volumeChange =
        clamp(
            numericLever(
                body.volume_change_pct,
            ),
            -90,
            500,
        );


    const priceChange =
        clamp(
            numericLever(
                body.list_price_change_pct,
            ),
            -90,
            500,
        );


    const discountChange =
        clamp(
            numericLever(
                body.discount_rate_change_pp,
            ),
            -95,
            95,
        );


    const costChange =
        clamp(
            numericLever(
                body.cost_per_unit_change_pct,
            ),
            -90,
            500,
        );


    const volumeFactor =
        1 +
        volumeChange /
            100;


    const priceFactor =
        1 +
        priceChange /
            100;


    const costFactor =
        1 +
        costChange /
            100;


    const baselineDiscount =
        clamp(
            baseline.discount_pct,
            0,
            95,
        );


    const baselineNetRetention =
        Math.max(
            0.000001,
            1 -
            baselineDiscount /
                100,
        );


    const baselineGrossSales =
        baseline.net_sales /
        baselineNetRetention;


    const baselineListPricePerUnit =
        baseline.units_sold >
        0
            ? baselineGrossSales /
                baseline.units_sold
            : 0;


    const scenarioUnits =
        Math.max(
            0,
            baseline.units_sold *
                volumeFactor,
        );


    const scenarioListPrice =
        Math.max(
            0,
            baselineListPricePerUnit *
                priceFactor,
        );


    const scenarioGrossSales =
        scenarioUnits *
        scenarioListPrice;


    const scenarioDiscountPct =
        clamp(
            baselineDiscount +
                discountChange,
            0,
            95,
        );


    const scenarioNetSales =
        scenarioGrossSales *
        (
            1 -
            scenarioDiscountPct /
                100
        );


    const scenarioCostPerUnit =
        Math.max(
            0,
            baseline.cost_per_unit *
                costFactor,
        );


    const scenarioCogs =
        scenarioUnits *
        scenarioCostPerUnit;


    const scenarioGrossProfit =
        scenarioNetSales -
        scenarioCogs;


    const scenarioMarginPct =
        scenarioNetSales !==
        0
            ? (
                scenarioGrossProfit /
                scenarioNetSales
            ) *
                100
            : 0;


    return {
        net_sales:
            roundMetric(
                scenarioNetSales,
            ),

        gross_profit:
            roundMetric(
                scenarioGrossProfit,
            ),

        margin_pct:
            roundMetric(
                scenarioMarginPct,
            ),

        units_sold:
            roundMetric(
                scenarioUnits,
            ),

        discount_pct:
            roundMetric(
                scenarioDiscountPct,
            ),

        cost_per_unit:
            roundMetric(
                scenarioCostPerUnit,
            ),

        gross_sales:
            roundMetric(
                scenarioGrossSales,
            ),

        cogs:
            roundMetric(
                scenarioCogs,
            ),
    };
}


async function buildScenarioContext() {

    const metadataPayload =
        await fetchFastApi(
            "/metadata",
        );


    const metadata =
        metadataInfo(
            metadataPayload,
        );


    const period =
        currentMonthPeriod(
            metadata.dataThrough,
        );


    const comparisonPeriod =
        previousMonthPeriod(
            period.start,
        );


    return {
        ...metadata,

        period,

        comparisonPeriod,

        scopes:
            buildScopes(
                metadata.regions,
            ),
    };
}


/*
 * Build the deterministic /analyze request.
 *
 * IMPORTANT:
 *
 * `overall` is a Scenario Lab UI scope. It is NOT an
 * analytics dimension accepted by FastAPI.
 *
 * National / Overall analysis therefore has:
 *
 *   - no dimension property
 *   - no region filter
 *
 * Regional analysis adds:
 *
 *   dimension: "region"
 *   filters.region: "<selected region>"
 *
 * This is what fixes the HTTP 422 error for National / Overall.
 */
function buildAnalysisRequest(
    scope: ScenarioScope,
    requiredMetrics: string[],
    period: Period,
    comparisonPeriod: Period,
): JsonRecord {

    const filters:
        Record<string, string> =
        {};


    if (
        scope.dimension ===
            "region"
        &&
        scope.value
    ) {

        filters.region =
            scope.value;
    }


    const analysisRequest:
        JsonRecord = {

        analysis_type:
            "summary",

        metrics:
            requiredMetrics,

        filters,

        period,

        comparison_period:
            comparisonPeriod,

        top_n:
            10,

        sort_direction:
            "desc",
    };


    /*
     * Only send dimension to FastAPI when a real
     * supported analytics dimension is being used.
     *
     * Never send:
     *
     *     dimension: "overall"
     */
    if (
        scope.dimension ===
        "region"
    ) {

        analysisRequest.dimension =
            "region";
    }


    return analysisRequest;
}


export async function GET() {

    try {

        const context =
            await buildScenarioContext();


        return NextResponse.json(
            {
                status:
                    "success",

                data_through:
                    context.dataThrough,

                baseline_period:
                    context.period,

                comparison_period:
                    context.comparisonPeriod,

                calculation_basis:
                    (
                        "Deterministic "
                        +
                        "selected-scope "
                        +
                        "sensitivity model"
                    ),

                scopes:
                    context.scopes,
            },
        );

    } catch (error) {

        const status =
            error instanceof
            UpstreamError
                ? error.statusCode
                : 500;


        return NextResponse.json(
            {
                status:
                    "error",

                detail:
                    error instanceof
                    Error
                        ? error.message
                        : (
                            "Scenario configuration "
                            +
                            "could not be loaded."
                        ),

                upstream:
                    error instanceof
                    UpstreamError
                        ? error.details
                        : null,
            },
            {
                status,
            },
        );
    }
}


export async function POST(
    request: NextRequest,
) {

    try {

        const body =
            (
                await request.json()
            ) as ScenarioRequestBody;


        const context =
            await buildScenarioContext();


        const requestedDimension =
            body.scope?.dimension ??
            "overall";


        let scope:
            ScenarioScope;


        if (
            requestedDimension ===
            "region"
        ) {

            const region =
                canonicalRegion(
                    body.scope?.value ??
                        null,
                    context.regions,
                );


            scope = {
                key:
                    `region:${region}`,

                label:
                    `${region} region`,

                dimension:
                    "region",

                value:
                    region,
            };

        } else {

            scope = {
                key:
                    "overall",

                label:
                    "National / Overall",

                dimension:
                    "overall",

                value:
                    null,
            };
        }


        const requiredMetrics = [
            "net_sales",
            "units_sold",
            "gross_profit",
            "discount_pct",
        ];


        const unsupported =
            requiredMetrics.filter(
                (
                    metric,
                ) =>
                    !context
                        .supportedMetrics
                        .includes(
                            metric,
                        ),
            );


        if (
            unsupported.length >
            0
        ) {

            throw new Error(
                (
                    "Scenario baseline requires "
                    +
                    "unsupported metrics: "
                    +
                    unsupported.join(
                        ", ",
                    )
                ),
            );
        }


        const analysisRequest =
            buildAnalysisRequest(
                scope,
                requiredMetrics,
                context.period,
                context.comparisonPeriod,
            );


        const analysisPayload =
            await fetchFastApi(
                "/analyze",
                {
                    method:
                        "POST",

                    body:
                        JSON.stringify(
                            analysisRequest,
                        ),
                },
            );


        const netSales =
            extractMetric(
                analysisPayload,
                "net_sales",
            );


        const unitsSold =
            extractMetric(
                analysisPayload,
                "units_sold",
            );


        const grossProfit =
            extractMetric(
                analysisPayload,
                "gross_profit",
            );


        const discountPct =
            extractMetric(
                analysisPayload,
                "discount_pct",
            );


        const marginPct =
            netSales !==
            0
                ? (
                    grossProfit /
                    netSales
                ) *
                    100
                : 0;


        const costPerUnit =
            unitsSold !==
            0
                ? (
                    netSales -
                    grossProfit
                ) /
                    unitsSold
                : 0;


        const baseline:
            BaselineMetrics = {

            net_sales:
                roundMetric(
                    netSales,
                ),

            gross_profit:
                roundMetric(
                    grossProfit,
                ),

            margin_pct:
                roundMetric(
                    marginPct,
                ),

            units_sold:
                roundMetric(
                    unitsSold,
                ),

            discount_pct:
                roundMetric(
                    discountPct,
                ),

            cost_per_unit:
                roundMetric(
                    costPerUnit,
                ),
        };


        const scenario =
            applyScenario(
                baseline,
                body,
            );


        return NextResponse.json(
            {
                status:
                    "success",

                scope,

                data_through:
                    context.dataThrough,

                baseline_period:
                    context.period,

                comparison_period:
                    context.comparisonPeriod,

                calculation_basis:
                    (
                        "Deterministic "
                        +
                        "selected-scope "
                        +
                        "sensitivity model"
                    ),

                baseline,

                levers: {
                    volume_change_pct:
                        numericLever(
                            body
                                .volume_change_pct,
                        ),

                    list_price_change_pct:
                        numericLever(
                            body
                                .list_price_change_pct,
                        ),

                    discount_rate_change_pp:
                        numericLever(
                            body
                                .discount_rate_change_pp,
                        ),

                    cost_per_unit_change_pct:
                        numericLever(
                            body
                                .cost_per_unit_change_pct,
                        ),
                },

                scenario,

                delta: {
                    net_sales:
                        roundMetric(
                            (
                                scenario
                                    .net_sales
                                -
                                baseline
                                    .net_sales
                            ),
                        ),

                    gross_profit:
                        roundMetric(
                            (
                                scenario
                                    .gross_profit
                                -
                                baseline
                                    .gross_profit
                            ),
                        ),

                    margin_pp:
                        roundMetric(
                            (
                                scenario
                                    .margin_pct
                                -
                                baseline
                                    .margin_pct
                            ),
                        ),

                    units_sold:
                        roundMetric(
                            (
                                scenario
                                    .units_sold
                                -
                                baseline
                                    .units_sold
                            ),
                        ),
                },
            },
        );

    } catch (error) {

        const status =
            error instanceof
            UpstreamError
                ? error.statusCode
                : 500;


        return NextResponse.json(
            {
                status:
                    "error",

                detail:
                    error instanceof
                    Error
                        ? error.message
                        : (
                            "Scenario calculation "
                            +
                            "failed."
                        ),

                upstream:
                    error instanceof
                    UpstreamError
                        ? error.details
                        : null,
            },
            {
                status,
            },
        );
    }
}