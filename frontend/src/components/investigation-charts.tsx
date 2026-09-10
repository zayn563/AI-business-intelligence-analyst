"use client";

import {

    Bar,
    BarChart,
    CartesianGrid,
    Cell,
    ReferenceLine,
    ResponsiveContainer,
    Tooltip,
    XAxis,
    YAxis,

} from "recharts";

import type {
    BreakdownRow,
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


function percentage(
    value: number | null,
): string {

    if (
        value
        ===
        null
    ) {

        return "—";
    }

    return (
        `${value > 0 ? "+" : ""}`
        +
        `${value.toFixed(1)}%`
    );
}


function percentagePoints(
    value: number | null,
): string {

    if (
        value
        ===
        null
    ) {

        return "—";
    }

    return (
        `${value > 0 ? "+" : ""}`
        +
        `${value.toFixed(1)} pp`
    );
}


// ============================================================
// CONTRIBUTION CHART
// ============================================================

export function ContributionChart(
    {
        rows,
    }: {
        rows:
            BreakdownRow[];
    },
) {

    if (
        rows.length
        ===
        0
    ) {

        return (

            <div className="empty-block">

                No contribution data is available for this dimension.

            </div>
        );
    }


    const chartRows =
        rows.slice(
            0,
            8,
        );


    return (

        <div className="interactive-chart investigation-chart">

            <ResponsiveContainer
                width="100%"
                height={
                    Math.max(
                        300,
                        chartRows.length
                        *
                        48,
                    )
                }
            >

                <BarChart
                    layout="vertical"
                    data={
                        chartRows
                    }
                    margin={{
                        top:
                            10,

                        right:
                            28,

                        bottom:
                            10,

                        left:
                            8,
                    }}
                >

                    <CartesianGrid
                        strokeDasharray="4 4"
                        horizontal={false}
                        stroke="var(--chart-grid)"
                    />


                    <XAxis
                        type="number"
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
                        tick={{
                            fontSize:
                                10,

                            fill:
                                "var(--muted-text)",
                        }}
                    />


                    <YAxis
                        type="category"
                        dataKey="entity"
                        width={165}
                        axisLine={false}
                        tickLine={false}
                        tick={{
                            fontSize:
                                10,

                            fill:
                                "var(--text)",
                        }}
                    />


                    <ReferenceLine
                        x={0}
                        stroke="var(--border-strong)"
                    />


                    <Tooltip
                        cursor={{
                            fill:
                                "rgba(15, 54, 40, 0.04)",
                        }}
                        content={
                            (
                                {
                                    active,
                                    payload,
                                },
                            ) => {

                                if (
                                    !active
                                    ||
                                    !payload
                                    ||
                                    payload.length
                                    ===
                                    0
                                ) {

                                    return null;
                                }


                                const row = (
                                    payload[
                                        0
                                    ]
                                    ?.payload
                                ) as BreakdownRow | undefined;


                                if (!row) {

                                    return null;
                                }


                                return (

                                    <div className="chart-tooltip">

                                        <strong>
                                            {
                                                row.entity
                                            }
                                        </strong>


                                        <div>

                                            <span>
                                                Current sales
                                            </span>

                                            <b>
                                                {
                                                    compactNumber(
                                                        row.current_sales,
                                                    )
                                                }
                                            </b>

                                        </div>


                                        <div>

                                            <span>
                                                Sales change
                                            </span>

                                            <b>
                                                {
                                                    percentage(
                                                        row.sales_change_pct,
                                                    )
                                                }
                                            </b>

                                        </div>


                                        <div>

                                            <span>
                                                Margin change
                                            </span>

                                            <b>
                                                {
                                                    percentagePoints(
                                                        row.margin_change_pp,
                                                    )
                                                }
                                            </b>

                                        </div>


                                        <div>

                                            <span>
                                                Units change
                                            </span>

                                            <b>
                                                {
                                                    percentage(
                                                        row.units_change_pct,
                                                    )
                                                }
                                            </b>

                                        </div>

                                    </div>
                                );
                            }
                        }
                    />


                    <Bar
                        dataKey="sales_change"
                        radius={[
                            0,
                            6,
                            6,
                            0,
                        ]}
                    >

                        {
                            chartRows.map(
                                (
                                    row,
                                ) => (

                                    <Cell
                                        key={
                                            row.entity
                                        }
                                        fill={
                                            row.sales_change
                                            <
                                            0
                                                ?
                                                "var(--chart-negative)"
                                                :
                                                "var(--chart-positive)"
                                        }
                                    />

                                ),
                            )
                        }

                    </Bar>

                </BarChart>

            </ResponsiveContainer>

        </div>
    );
}