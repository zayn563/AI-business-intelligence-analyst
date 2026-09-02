"use client";

import Link
from "next/link";

import {
    useState,
} from "react";

import type {
    FormEvent,
} from "react";

import {

    RegionPerformanceChart,
    SalesTrendChart,

} from "@/components/business-charts";

import type {

    AnalystResponse,
    BusinessPriority,
    ComparisonKpi,
    DashboardData,

} from "@/lib/types";


// ============================================================
// PROPS
// ============================================================

type Props = {

    initialData:
        DashboardData;
};


// ============================================================
// FORMATTERS
// ============================================================

function formatDate(
    value?: string | null,
): string {

    if (!value) {

        return "—";
    }

    const parsed =
        new Date(
            `${value}T00:00:00`,
        );

    if (
        Number.isNaN(
            parsed.getTime(),
        )
    ) {

        return value;
    }

    return new Intl.DateTimeFormat(
        "en-US",
        {
            month:
                "short",

            day:
                "numeric",

            year:
                "numeric",
        },
    ).format(
        parsed,
    );
}


function compact(
    value?: number | null,
): string {

    if (
        value
        ===
        null
        ||
        value
        ===
        undefined
    ) {

        return "—";
    }

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


function humanize(
    value?: string | null,
): string {

    if (!value) {

        return "Not classified";
    }

    return value
        .replaceAll(
            "_",
            " ",
        )
        .replace(
            /\b\w/g,
            (
                character,
            ) =>
                character
                    .toUpperCase(),
        );
}


// ============================================================
// KPI HELPERS
// ============================================================

function kpiValue(
    key: string,
    kpi: ComparisonKpi,
): string {

    if (
        key
        ===
        "margin_pct"
        ||
        key
        ===
        "target_attainment"
    ) {

        return (
            kpi.current
            !==
            null
            &&
            kpi.current
            !==
            undefined
                ?
                `${kpi.current.toFixed(1)}%`
                :
                "—"
        );
    }

    return compact(
        kpi.current,
    );
}


function kpiChange(
    kpi: ComparisonKpi,
): string | null {

    if (
        kpi.change_pp
        !==
        null
        &&
        kpi.change_pp
        !==
        undefined
    ) {

        return (
            `${kpi.change_pp > 0 ? "+" : ""}`
            +
            `${kpi.change_pp.toFixed(2)} pp`
        );
    }


    if (
        kpi.change_pct
        !==
        null
        &&
        kpi.change_pct
        !==
        undefined
    ) {

        return (
            `${kpi.change_pct > 0 ? "+" : ""}`
            +
            `${kpi.change_pct.toFixed(2)}%`
        );
    }

    return null;
}


function kpiClass(
    kpi: ComparisonKpi,
): string {

    if (
        kpi.direction
        ===
        "increase"
    ) {

        return "change-positive";
    }

    if (
        kpi.direction
        ===
        "decrease"
    ) {

        return "change-negative";
    }

    return "change-neutral";
}


// ============================================================
// PRIORITY CARD
// ============================================================

function PriorityCard(
    {
        priority,
    }: {
        priority:
            BusinessPriority;
    },
) {

    const risk =
        priority.type
        ===
        "risk";


    return (

        <article
            className={
                risk
                    ?
                    "decision-card decision-risk"
                    :
                    "decision-card decision-opportunity"
            }
        >

            <div className="decision-card-top">

                <div>

                    <div
                        className={
                            risk
                                ?
                                "priority-type risk"
                                :
                                "priority-type opportunity"
                        }
                    >

                        {
                            risk
                                ?
                                "Needs attention"
                                :
                                "Opportunity"
                        }

                    </div>


                    <h3>
                        {priority.title}
                    </h3>

                </div>


                <strong
                    className={
                        risk
                            ?
                            "primary-change negative"
                            :
                            "primary-change positive"
                    }
                >

                    {
                        priority.primary_change
                    }

                </strong>

            </div>


            {
                priority.lifecycle_status
                &&
                (

                    <div className="lifecycle-line">

                        <span>
                            Status
                        </span>

                        <strong>
                            {
                                priority.lifecycle_status
                            }
                        </strong>

                    </div>

                )
            }


            <div className="evidence-row">

                {
                    priority.evidence.map(
                        (
                            evidence,
                        ) => (

                            <div
                                className="evidence-chip"
                                key={
                                    evidence.metric
                                }
                            >

                                <span>
                                    {
                                        evidence.label
                                    }
                                </span>

                                <strong>
                                    {
                                        evidence.change
                                    }
                                </strong>

                            </div>

                        ),
                    )
                }

            </div>


            <div className="driver-line">

                <span>
                    Likely driver
                </span>

                <strong>
                    {
                        humanize(
                            priority.diagnosis,
                        )
                    }
                </strong>

            </div>


            <div className="recommended-action">

                <span>
                    Recommended next step
                </span>

                <p>
                    {
                        priority
                            .recommended_action
                    }
                </p>

            </div>


            {
                priority.insight_id
                ?
                (

                    <Link
                        className="investigate-button"
                        href={
                            `/investigate/${priority.insight_id}`
                        }
                    >

                        Open investigation →

                    </Link>

                )
                :
                null
            }

        </article>
    );
}


// ============================================================
// MAIN COMPONENT
// ============================================================

export default function DashboardClient(
    {
        initialData,
    }: Props,
) {

    const summary =
        initialData.summary;


    const [
        question,
        setQuestion,
    ] =
        useState(
            "",
        );


    const [
        analystResult,
        setAnalystResult,
    ] =
        useState<
            AnalystResponse | null
        >(
            null,
        );


    const [
        loading,
        setLoading,
    ] =
        useState(
            false,
        );


    if (!summary) {

        return (

            <main className="app-shell">

                <div className="fatal-state">

                    <h1>
                        Dashboard unavailable
                    </h1>

                    <p>
                        Start the FastAPI backend and refresh this page.
                    </p>

                </div>

            </main>
        );
    }


    // ========================================================
    // ANALYST
    // ========================================================

    async function askAnalyst(
        override?: string,
    ) {

        const finalQuestion =
            (
                override
                ??
                question
            )
            .trim();


        if (!finalQuestion) {

            return;
        }


        setQuestion(
            finalQuestion,
        );

        setLoading(
            true,
        );

        setAnalystResult(
            null,
        );


        try {

            const response =
                await fetch(
                    "/api/analyst",
                    {
                        method:
                            "POST",

                        headers: {
                            "Content-Type":
                                "application/json",
                        },

                        body:
                            JSON.stringify(
                                {
                                    question:
                                        finalQuestion,
                                },
                            ),
                    },
                );


            const payload = (
                await response.json()
            ) as AnalystResponse;


            setAnalystResult(
                payload,
            );

        }
        finally {

            setLoading(
                false,
            );
        }
    }


    function submit(
        event:
            FormEvent<HTMLFormElement>,
    ) {

        event.preventDefault();

        void askAnalyst();
    }


    // ========================================================
    // KPI COLLECTION
    // ========================================================

    const kpis = [

        {
            key:
                "net_sales",

            data:
                summary
                    .kpis
                    .net_sales,
        },

        {
            key:
                "gross_profit",

            data:
                summary
                    .kpis
                    .gross_profit,
        },

        {
            key:
                "margin_pct",

            data:
                summary
                    .kpis
                    .margin_pct,
        },

        {
            key:
                "units_sold",

            data:
                summary
                    .kpis
                    .units_sold,
        },

        {
            key:
                "target_attainment",

            data:
                summary
                    .kpis
                    .target_attainment,
        },
    ];


    // ========================================================
    // UI
    // ========================================================

    return (

        <main className="app-shell">

            {/* =================================================
                HEADER
            ================================================= */}

            <header className="business-header">

                <div>

                    <span className="eyebrow">

                        COMMERCIAL DECISION INTELLIGENCE

                    </span>


                    <h1>

                        AI Business Intelligence Analyst

                    </h1>


                    <p>

                        Monitor the business, understand what matters
                        and move from diagnosis to action.

                    </p>

                </div>


                <div className="data-freshness">

                    <span>
                        Data through
                    </span>

                    <strong>
                        {
                            formatDate(
                                summary.data_through,
                            )
                        }
                    </strong>

                </div>

            </header>


            {/* =================================================
                BUSINESS BRIEF
            ================================================= */}

            <section className="morning-brief">

                <div className="brief-summary">

                    <span className="section-kicker">
                        BUSINESS BRIEF
                    </span>

                    <h2>
                        {
                            summary
                                .brief
                                .headline
                        }
                    </h2>


                    <div className="brief-counts">

                        <div>

                            <strong>
                                {
                                    summary
                                        .brief
                                        .risk_count
                                }
                            </strong>

                            <span>
                                active risks
                            </span>

                        </div>


                        <div>

                            <strong>
                                {
                                    summary
                                        .brief
                                        .opportunity_count
                                }
                            </strong>

                            <span>
                                opportunities
                            </span>

                        </div>

                    </div>


                    <Link
                        href="/priorities"
                        className="brief-all-link"
                    >

                        View all priorities →

                    </Link>

                </div>


                {
                    summary
                        .brief
                        .recommended_focus
                    &&
                    (

                        <div className="brief-focus">

                            <span>
                                Recommended management focus
                            </span>


                            <strong>
                                {
                                    summary
                                        .brief
                                        .recommended_focus
                                        ?.title
                                }
                            </strong>


                            <p>
                                {
                                    summary
                                        .brief
                                        .recommended_focus
                                        ?.recommended_action
                                }
                            </p>


                            {
                                summary
                                    .brief
                                    .recommended_focus
                                    ?.insight_id
                                &&
                                (

                                    <Link
                                        href={
                                            `/investigate/${summary.brief.recommended_focus.insight_id}`
                                        }
                                    >

                                        Investigate priority →

                                    </Link>

                                )
                            }

                        </div>

                    )
                }

            </section>


            {/* =================================================
                KPI
            ================================================= */}

            <section>

                <div className="section-heading">

                    <div>

                        <span className="section-kicker">
                            BUSINESS PERFORMANCE
                        </span>

                        <h2>
                            Executive overview
                        </h2>

                    </div>

                </div>


                <div className="business-kpi-grid">

                    {
                        kpis.map(
                            (
                                item,
                            ) => {

                                const change =
                                    kpiChange(
                                        item.data,
                                    );


                                return (

                                    <article
                                        className="business-kpi"
                                        key={
                                            item.key
                                        }
                                    >

                                        <span className="business-kpi-label">

                                            {
                                                item.data.label
                                            }

                                        </span>


                                        <strong className="business-kpi-value">

                                            {
                                                kpiValue(
                                                    item.key,
                                                    item.data,
                                                )
                                            }

                                        </strong>


                                        {
                                            change
                                            ?
                                            (

                                                <span
                                                    className={
                                                        `business-kpi-change ${kpiClass(item.data)}`
                                                    }
                                                >

                                                    {change}
                                                    {" "}
                                                    vs previous period

                                                </span>

                                            )
                                            :
                                            (

                                                <span className="business-kpi-change change-neutral">

                                                    Current-period performance

                                                </span>

                                            )
                                        }

                                    </article>

                                );

                            },
                        )
                    }

                </div>

            </section>


            {/* =================================================
                RISKS
            ================================================= */}

            <section>

                <div className="section-heading">

                    <div>

                        <span className="section-kicker">
                            WHAT NEEDS ATTENTION
                        </span>

                        <h2>
                            Management priorities
                        </h2>

                    </div>


                    <Link
                        href="/priorities"
                        className="section-action-link"
                    >

                        View priority center →

                    </Link>

                </div>


                <div className="decision-grid">

                    {
                        summary
                            .priorities
                            .risks
                            .map(
                                (
                                    priority,
                                ) => (

                                    <PriorityCard
                                        key={
                                            priority.fingerprint
                                        }
                                        priority={
                                            priority
                                        }
                                    />

                                ),
                            )
                    }

                </div>

            </section>


            {/* =================================================
                OPPORTUNITIES
            ================================================= */}

            {
                summary
                    .priorities
                    .opportunities
                    .length
                >
                0
                &&
                (

                    <section>

                        <div className="section-heading">

                            <div>

                                <span className="section-kicker">
                                    GROWTH OPPORTUNITIES
                                </span>

                                <h2>
                                    Positive signals worth exploring
                                </h2>

                            </div>

                        </div>


                        <div className="decision-grid">

                            {
                                summary
                                    .priorities
                                    .opportunities
                                    .map(
                                        (
                                            priority,
                                        ) => (

                                            <PriorityCard
                                                key={
                                                    priority.fingerprint
                                                }
                                                priority={
                                                    priority
                                                }
                                            />

                                        ),
                                    )
                            }

                        </div>

                    </section>

                )
            }


            {/* =================================================
                INTERACTIVE ANALYTICS
            ================================================= */}

            <section>

                <div className="section-heading">

                    <div>

                        <span className="section-kicker">
                            INTERACTIVE PERFORMANCE
                        </span>

                        <h2>
                            Explore recent business movement
                        </h2>

                    </div>

                    <span className="chart-help">

                        Hover over the charts for detailed values.

                    </span>

                </div>


                <div className="analytics-grid">

                    <article className="analytics-panel">

                        <div className="chart-heading">

                            <div>

                                <span className="section-kicker">
                                    PERFORMANCE TREND
                                </span>

                                <h3>
                                    Sales & gross profit
                                </h3>

                            </div>

                        </div>


                        <SalesTrendChart
                            points={
                                summary.trend
                            }
                        />

                    </article>


                    <article className="analytics-panel">

                        <div className="chart-heading">

                            <div>

                                <span className="section-kicker">
                                    REGION PERFORMANCE
                                </span>

                                <h3>
                                    Sales & target attainment
                                </h3>

                            </div>

                        </div>


                        <RegionPerformanceChart
                            regions={
                                summary.regions
                            }
                        />

                    </article>

                </div>

            </section>


            {/* =================================================
                REGION TABLE
            ================================================= */}

            <section className="region-detail-panel">

                <div className="section-heading compact">

                    <div>

                        <span className="section-kicker">
                            REGION DETAIL
                        </span>

                        <h2>
                            Latest month
                        </h2>

                    </div>

                </div>


                <div className="region-table">

                    <div className="region-row region-header">

                        <span>
                            Region
                        </span>

                        <span>
                            Sales
                        </span>

                        <span>
                            Change
                        </span>

                        <span>
                            Target
                        </span>

                    </div>


                    {
                        summary.regions.map(
                            (
                                region,
                            ) => (

                                <div
                                    className="region-row"
                                    key={
                                        region.region
                                    }
                                >

                                    <strong>
                                        {
                                            region.region
                                        }
                                    </strong>


                                    <span>
                                        {
                                            compact(
                                                region.net_sales,
                                            )
                                        }
                                    </span>


                                    <span
                                        className={
                                            (
                                                region.sales_change_pct
                                                ??
                                                0
                                            )
                                            >=
                                            0
                                                ?
                                                "table-positive"
                                                :
                                                "table-negative"
                                        }
                                    >

                                        {
                                            region.sales_change_pct
                                            !==
                                            null
                                                ?
                                                (
                                                    `${region.sales_change_pct > 0 ? "+" : ""}`
                                                    +
                                                    `${region.sales_change_pct.toFixed(1)}%`
                                                )
                                                :
                                                "—"
                                        }

                                    </span>


                                    <span>

                                        {
                                            region.target_attainment_pct
                                            !==
                                            null
                                                ?
                                                `${region.target_attainment_pct.toFixed(1)}%`
                                                :
                                                "—"
                                        }

                                    </span>

                                </div>

                            ),
                        )
                    }

                </div>

            </section>


            {/* =================================================
                ANALYST
            ================================================= */}

            <section className="analyst-panel">

                <span className="section-kicker analyst-kicker">
                    ASK YOUR BUSINESS
                </span>


                <h2>
                    Investigate a follow-up question
                </h2>


                <p>

                    Use the analyst for questions not already
                    answered by the monitoring and investigation workflow.

                </p>


                <form
                    className="analyst-form"
                    onSubmit={
                        submit
                    }
                >

                    <textarea
                        value={
                            question
                        }
                        onChange={
                            (
                                event,
                            ) =>
                                setQuestion(
                                    event
                                        .target
                                        .value,
                                )
                        }
                        rows={
                            3
                        }
                        placeholder="Ask a business question..."
                    />


                    <button
                        type="submit"
                        disabled={
                            loading
                            ||
                            !question.trim()
                        }
                    >

                        {
                            loading
                                ?
                                "Analyzing..."
                                :
                                "Analyze"
                        }

                    </button>

                </form>


                {
                    loading
                    &&
                    (

                        <div className="analysis-loading">

                            Analyzing verified business evidence...

                        </div>

                    )
                }


                {
                    analystResult?.answer
                    &&
                    (

                        <div className="analysis-result">

                            <span>
                                ANALYST ANSWER
                            </span>

                            <p>
                                {
                                    analystResult.answer
                                }
                            </p>

                        </div>

                    )
                }

            </section>


            <footer>

                AI Business Intelligence Analyst ·
                Autonomous decision-intelligence platform

            </footer>

        </main>
    );
}