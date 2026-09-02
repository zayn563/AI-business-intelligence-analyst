import Link
from "next/link";

import {
    notFound,
} from "next/navigation";

import ActionPanel
from "@/components/action-panel";

import {
    ContributionChart,
} from "@/components/investigation-charts";

import {
    getInvestigation,
} from "@/lib/backend";


// ============================================================
// FORMATTERS
// ============================================================

function compact(
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


function humanize(
    value: string,
): string {

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
// PAGE
// ============================================================

export default async function InvestigationPage(
    {
        params,
    }: {
        params:
            Promise<{
                id: string;
            }>;
    },
) {

    const {
        id,
    } =
        await params;


    const insightId =
        Number(
            id,
        );


    if (
        !Number.isFinite(
            insightId,
        )
    ) {

        notFound();
    }


    const data =
        await getInvestigation(
            insightId,
        );


    if (!data) {

        notFound();
    }


    return (

        <main className="app-shell">

            {/* =================================================
                HEADER
            ================================================= */}

            <header className="investigation-header">

                <div>

                    <span className="section-kicker">

                        INVESTIGATION WORKSPACE

                    </span>


                    <h1>

                        {
                            data
                                .insight
                                .title
                        }

                    </h1>


                    <p>

                        {
                            data
                                .insight
                                .entity
                        }

                        {" · "}

                        {
                            data
                                .insight
                                .primary_change
                        }

                    </p>

                </div>


                <span
                    className={
                        (
                            "lifecycle-badge "
                            +
                            "lifecycle-"
                            +
                            (
                                data
                                    .insight
                                    .lifecycle_status
                                ??
                                "NEW"
                            )
                            .toLowerCase()
                        )
                    }
                >

                    {
                        data
                            .insight
                            .lifecycle_status
                        ??
                        "NEW"
                    }

                </span>

            </header>


            {/* =================================================
                PERIOD CONTEXT
            ================================================= */}

            <section className="scenario-scope-panel">

                <div className="scenario-basis-grid">

                    <div className="scenario-basis-item">

                        <span>
                            Current period
                        </span>

                        <strong>

                            {
                                data
                                    .period
                                    .current_start
                            }

                            {" — "}

                            {
                                data
                                    .period
                                    .current_end
                            }

                        </strong>

                    </div>


                    <div className="scenario-basis-item">

                        <span>
                            Comparison period
                        </span>

                        <strong>

                            {
                                data
                                    .period
                                    .comparison_start
                            }

                            {" — "}

                            {
                                data
                                    .period
                                    .comparison_end
                            }

                        </strong>

                    </div>


                    <div className="scenario-basis-item">

                        <span>
                            Scope
                        </span>

                        <strong>

                            {
                                humanize(
                                    data
                                        .insight
                                        .dimension,
                                )
                            }

                            {" · "}

                            {
                                data
                                    .insight
                                    .entity
                            }

                        </strong>

                    </div>

                </div>

            </section>


            {/* =================================================
                DIAGNOSIS
            ================================================= */}

            <section className="diagnosis-panel">

                <div>

                    <span>
                        Primary diagnosis
                    </span>

                    <strong>

                        {
                            humanize(
                                data
                                    .insight
                                    .diagnosis
                                ??
                                "mixed_or_unexplained",
                            )
                        }

                    </strong>

                </div>


                <div>

                    <span>
                        Severity
                    </span>

                    <strong>

                        {
                            humanize(
                                data
                                    .insight
                                    .severity,
                            )
                        }

                    </strong>

                </div>


                <div>

                    <span>
                        Priority score
                    </span>

                    <strong>

                        {
                            data
                                .insight
                                .priority_score
                                .toFixed(
                                    0,
                                )
                        }

                    </strong>

                </div>

            </section>


            {/* =================================================
                VERIFIED EVIDENCE
            ================================================= */}

            <section>

                <div className="section-heading">

                    <div>

                        <span className="section-kicker">

                            VERIFIED EVIDENCE

                        </span>

                        <h2>
                            What changed?
                        </h2>

                    </div>

                </div>


                <div className="investigation-evidence-grid">

                    {
                        data
                            .insight
                            .evidence
                            .map(
                                (
                                    item,
                                ) => (

                                    <article
                                        key={
                                            item.metric
                                        }
                                    >

                                        <span>

                                            {
                                                item.label
                                            }

                                        </span>


                                        <strong>

                                            {
                                                item.change
                                            }

                                        </strong>

                                    </article>

                                ),
                            )
                    }

                </div>

            </section>


            {/* =================================================
                CONTRIBUTION BREAKDOWNS
            ================================================= */}

            {
                Object
                    .entries(
                        data.breakdowns,
                    )
                    .filter(
                        (
                            [
                                ,
                                rows,
                            ],
                        ) =>
                            rows.length
                            >
                            0,
                    )
                    .map(
                        (
                            [
                                dimension,
                                rows,
                            ],
                        ) => (

                            <section
                                className="breakdown-panel"
                                key={
                                    dimension
                                }
                            >

                                <div className="section-heading">

                                    <div>

                                        <span className="section-kicker">

                                            CONTRIBUTION ANALYSIS

                                        </span>


                                        <h2>

                                            Top{" "}

                                            {
                                                humanize(
                                                    dimension,
                                                )
                                            }

                                            {" "}contributors

                                        </h2>

                                    </div>


                                    <span className="chart-help">

                                        Hover over bars for driver detail.

                                    </span>

                                </div>


                                <ContributionChart
                                    rows={
                                        rows
                                    }
                                />


                                <div className="breakdown-table">

                                    <div className="breakdown-row breakdown-header">

                                        <span>

                                            {
                                                humanize(
                                                    dimension,
                                                )
                                            }

                                        </span>

                                        <span>
                                            Sales
                                        </span>

                                        <span>
                                            Sales Δ
                                        </span>

                                        <span>
                                            Margin Δ
                                        </span>

                                        <span>
                                            Units Δ
                                        </span>

                                    </div>


                                    {
                                        rows.map(
                                            (
                                                row,
                                            ) => (

                                                <div
                                                    className="breakdown-row"
                                                    key={
                                                        row.entity
                                                    }
                                                >

                                                    <strong>

                                                        {
                                                            row.entity
                                                        }

                                                    </strong>


                                                    <span>

                                                        {
                                                            compact(
                                                                row.current_sales,
                                                            )
                                                        }

                                                    </span>


                                                    <span
                                                        className={
                                                            (
                                                                row
                                                                    .sales_change_pct
                                                                ??
                                                                0
                                                            )
                                                            <
                                                            0
                                                                ?
                                                                "table-negative"
                                                                :
                                                                "table-positive"
                                                        }
                                                    >

                                                        {
                                                            row
                                                                .sales_change_pct
                                                            !==
                                                            null
                                                                ?
                                                                (
                                                                    `${row.sales_change_pct > 0 ? "+" : ""}`
                                                                    +
                                                                    `${row.sales_change_pct.toFixed(1)}%`
                                                                )
                                                                :
                                                                "—"
                                                        }

                                                    </span>


                                                    <span>

                                                        {
                                                            row
                                                                .margin_change_pp
                                                            !==
                                                            null
                                                                ?
                                                                (
                                                                    `${row.margin_change_pp > 0 ? "+" : ""}`
                                                                    +
                                                                    `${row.margin_change_pp.toFixed(1)} pp`
                                                                )
                                                                :
                                                                "—"
                                                        }

                                                    </span>


                                                    <span>

                                                        {
                                                            row
                                                                .units_change_pct
                                                            !==
                                                            null
                                                                ?
                                                                (
                                                                    `${row.units_change_pct > 0 ? "+" : ""}`
                                                                    +
                                                                    `${row.units_change_pct.toFixed(1)}%`
                                                                )
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

                        ),
                    )
            }


            {/* =================================================
                RECOMMENDATIONS
            ================================================= */}

            <section>

                <div className="section-heading">

                    <div>

                        <span className="section-kicker">

                            DECISION SUPPORT

                        </span>

                        <h2>
                            Recommended actions
                        </h2>

                    </div>

                </div>


                <div className="recommendation-grid">

                    {
                        data
                            .recommendations
                            .map(
                                (
                                    recommendation,
                                    index,
                                ) => (

                                    <article
                                        key={
                                            (
                                                recommendation.title
                                                +
                                                index
                                            )
                                        }
                                    >

                                        <span>

                                            {
                                                index
                                                +
                                                1
                                            }

                                        </span>


                                        <div>

                                            <div className="recommendation-priority">

                                                {
                                                    recommendation.priority
                                                }

                                            </div>


                                            <strong>

                                                {
                                                    recommendation.title
                                                }

                                            </strong>


                                            <p>

                                                {
                                                    recommendation.reason
                                                }

                                            </p>

                                        </div>

                                    </article>

                                ),
                            )
                    }

                </div>


                <Link
                    className="scenario-cta"
                    href={
                        (
                            `/scenario?insight_id=`
                            +
                            insightId
                        )
                    }
                >

                    Model a recovery scenario →

                </Link>

            </section>


            {/* =================================================
                ACTION TRACKER
            ================================================= */}

            <ActionPanel
                insightId={
                    insightId
                }
            />

        </main>
    );
}