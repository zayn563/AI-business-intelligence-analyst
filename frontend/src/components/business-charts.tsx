"use client";

import {

    Bar,
    CartesianGrid,
    ComposedChart,
    Legend,
    Line,
    LineChart,
    ResponsiveContainer,
    Tooltip,
    XAxis,
    YAxis,

} from "recharts";

import type {

    RegionPerformance,
    TrendPoint,

} from "@/lib/types";


// ============================================================
// FORMATTERS
// ============================================================

function compactNumber(
    value: number,
): string {

    return new Intl.NumberFormat(
        "en-US",
        {
            notation:
                "compact",

            maximumFractionDigits:
                2,
        },
    ).format(
        value,
    );
}


function moneyTooltip(
    value: unknown,
): string {

    const numericValue =
        Number(
            value,
        );

    if (
        Number.isNaN(
            numericValue,
        )
    ) {

        return "—";
    }

    return new Intl.NumberFormat(
        "en-US",
        {
            maximumFractionDigits:
                2,
        },
    ).format(
        numericValue,
    );
}


function formatMonth(
    value: string,
): string {

    const date =
        new Date(
            `${value}T00:00:00`,
        );

    if (
        Number.isNaN(
            date.getTime(),
        )
    ) {

        return value;
    }

    return date.toLocaleDateString(
        "en-US",
        {
            month:
                "short",

            year:
                "numeric",
        },
    );
}


// ============================================================
// SALES TREND
// ============================================================

export function SalesTrendChart(
    {
        points,
    }: {
        points:
            TrendPoint[];
    },
) {

    if (
        points.length
        ===
        0
    ) {

        return (

            <div className="empty-block">

                Trend data is not available.

            </div>
        );
    }


    return (

        <div className="interactive-chart">

            <ResponsiveContainer
                width="100%"
                height={320}
            >

                <LineChart
                    data={
                        points
                    }
                    margin={{
                        top:
                            20,

                        right:
                            18,

                        bottom:
                            10,

                        left:
                            2,
                    }}
                >

                    <CartesianGrid
                        strokeDasharray="4 4"
                        vertical={false}
                        stroke="var(--chart-grid)"
                    />


                    <XAxis
                        dataKey="month"
                        tickFormatter={
                            (
                                value,
                            ) =>
                                new Date(
                                    `${value}T00:00:00`,
                                )
                                    .toLocaleDateString(
                                        "en-US",
                                        {
                                            month:
                                                "short",
                                        },
                                    )
                        }
                        axisLine={false}
                        tickLine={false}
                        tick={{
                            fontSize:
                                11,

                            fill:
                                "var(--muted-text)",
                        }}
                    />


                    <YAxis
                        tickFormatter={
                            (
                                value,
                            ) =>
                                compactNumber(
                                    Number(
                                        value,
                                    ),
                                )
                        }
                        axisLine={false}
                        tickLine={false}
                        width={55}
                        tick={{
                            fontSize:
                                11,

                            fill:
                                "var(--muted-text)",
                        }}
                    />


                    <Tooltip
                        labelFormatter={
                            (
                                label,
                            ) =>
                                formatMonth(
                                    String(
                                        label,
                                    ),
                                )
                        }
                        formatter={
                            (
                                value,
                                name,
                            ) => {

                                const label =
                                    name
                                    ===
                                    "Net sales"
                                        ?
                                        "Net sales"
                                        :
                                        "Gross profit";

                                return [
                                    moneyTooltip(
                                        value,
                                    ),
                                    label,
                                ];
                            }
                        }
                        contentStyle={{
                            borderRadius:
                                "12px",

                            border:
                                "1px solid var(--border)",

                            boxShadow:
                                "0 10px 35px rgba(0,0,0,0.10)",
                        }}
                    />


                    <Legend
                        verticalAlign="top"
                        align="right"
                        height={34}
                    />


                    <Line
                        name="Net sales"
                        type="monotone"
                        dataKey="net_sales"
                        stroke="var(--chart-primary)"
                        strokeWidth={3}
                        dot={{
                            r:
                                4,

                            fill:
                                "var(--chart-accent)",

                            stroke:
                                "var(--chart-primary)",

                            strokeWidth:
                                2,
                        }}
                        activeDot={{
                            r:
                                7,
                        }}
                    />


                    <Line
                        name="Gross profit"
                        type="monotone"
                        dataKey="gross_profit"
                        stroke="var(--chart-secondary)"
                        strokeWidth={2}
                        strokeDasharray="6 5"
                        dot={false}
                        activeDot={{
                            r:
                                5,
                        }}
                    />

                </LineChart>

            </ResponsiveContainer>

        </div>
    );
}


// ============================================================
// REGION PERFORMANCE
// ============================================================

export function RegionPerformanceChart(
    {
        regions,
    }: {
        regions:
            RegionPerformance[];
    },
) {

    if (
        regions.length
        ===
        0
    ) {

        return (

            <div className="empty-block">

                Regional data is not available.

            </div>
        );
    }


    return (

        <div className="interactive-chart">

            <ResponsiveContainer
                width="100%"
                height={320}
            >

                <ComposedChart
                    data={
                        regions
                    }
                    margin={{
                        top:
                            20,

                        right:
                            12,

                        bottom:
                            10,

                        left:
                            0,
                    }}
                >

                    <CartesianGrid
                        strokeDasharray="4 4"
                        vertical={false}
                        stroke="var(--chart-grid)"
                    />


                    <XAxis
                        dataKey="region"
                        axisLine={false}
                        tickLine={false}
                        tick={{
                            fontSize:
                                11,

                            fill:
                                "var(--muted-text)",
                        }}
                    />


                    <YAxis
                        yAxisId="sales"
                        tickFormatter={
                            (
                                value,
                            ) =>
                                compactNumber(
                                    Number(
                                        value,
                                    ),
                                )
                        }
                        axisLine={false}
                        tickLine={false}
                        width={55}
                        tick={{
                            fontSize:
                                11,

                            fill:
                                "var(--muted-text)",
                        }}
                    />


                    <YAxis
                        yAxisId="target"
                        orientation="right"
                        domain={[
                            0,
                            120,
                        ]}
                        tickFormatter={
                            (
                                value,
                            ) =>
                                `${value}%`
                        }
                        axisLine={false}
                        tickLine={false}
                        width={45}
                        tick={{
                            fontSize:
                                10,

                            fill:
                                "var(--muted-text)",
                        }}
                    />


                    <Tooltip
                        formatter={
                            (
                                value,
                                name,
                            ) => {

                                if (
                                    name
                                    ===
                                    "Target attainment"
                                ) {

                                    const numeric =
                                        Number(
                                            value,
                                        );

                                    return [
                                        Number.isNaN(
                                            numeric,
                                        )
                                            ?
                                            "—"
                                            :
                                            `${numeric.toFixed(1)}%`,
                                        "Target attainment",
                                    ];
                                }

                                return [
                                    moneyTooltip(
                                        value,
                                    ),
                                    "Net sales",
                                ];
                            }
                        }
                        contentStyle={{
                            borderRadius:
                                "12px",

                            border:
                                "1px solid var(--border)",

                            boxShadow:
                                "0 10px 35px rgba(0,0,0,0.10)",
                        }}
                    />


                    <Legend
                        verticalAlign="top"
                        align="right"
                        height={34}
                    />


                    <Bar
                        name="Net sales"
                        yAxisId="sales"
                        dataKey="net_sales"
                        fill="var(--chart-primary)"
                        radius={[
                            6,
                            6,
                            0,
                            0,
                        ]}
                        maxBarSize={52}
                    />


                    <Line
                        name="Target attainment"
                        yAxisId="target"
                        type="monotone"
                        dataKey="target_attainment_pct"
                        stroke="var(--chart-accent-strong)"
                        strokeWidth={3}
                        connectNulls={false}
                        dot={{
                            r:
                                4,

                            fill:
                                "var(--chart-accent)",

                            stroke:
                                "var(--chart-accent-strong)",

                            strokeWidth:
                                2,
                        }}
                    />

                </ComposedChart>

            </ResponsiveContainer>

        </div>
    );
}