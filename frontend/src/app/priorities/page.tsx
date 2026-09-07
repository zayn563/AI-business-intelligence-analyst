import Link
from "next/link";

import {
    getPriorities,
} from "@/lib/backend";

import type {
    BusinessPriority,
} from "@/lib/types";


// ============================================================
// HELPERS
// ============================================================

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


function datasetList(
    values?: string[] | null,
): string {

    if (
        !values
        ||
        values.length ===
            0
    ) {

        return "";
    }

    return values
        .map(
            humanize,
        )
        .join(
            ", ",
        );
}


function isResolved(
    insight:
        BusinessPriority,
): boolean {

    return (
        (
            insight
                .lifecycle_status
            ??
            ""
        )
        .toUpperCase()
        ===
        "RESOLVED"
    );
}


function isBlocked(
    insight:
        BusinessPriority,
): boolean {

    return (
        !isResolved(
            insight,
        )
        &&
        insight
            .resolution_blocked
        ===
        true
    );
}


function evidenceLabel(
    insight:
        BusinessPriority,
): string {

    if (
        isResolved(
            insight,
        )
    ) {

        return "Resolved";
    }

    if (
        isBlocked(
            insight,
        )
    ) {

        return "Evidence pending";
    }

    if (
        insight
            .evidence_status
    ) {

        return humanize(
            insight
                .evidence_status,
        );
    }

    return "Evidence current";
}


function evidenceClass(
    insight:
        BusinessPriority,
): string {

    if (
        isResolved(
            insight,
        )
    ) {

        return (
            "evidence-state-badge "
            +
            "evidence-state-neutral"
        );
    }

    if (
        isBlocked(
            insight,
        )
    ) {

        return (
            "evidence-state-badge "
            +
            "evidence-state-pending"
        );
    }

    return (
        "evidence-state-badge "
        +
        "evidence-state-current"
    );
}


function evidenceDetail(
    insight:
        BusinessPriority,
): string {

    if (
        isBlocked(
            insight,
        )
    ) {

        const blockers =
            datasetList(
                insight
                    .blocking_datasets,
            );

        return (
            blockers
                ?
                `${blockers} · resolution held`
                :
                "Required evidence is not current"
        );
    }

    const required =
        datasetList(
            insight
                .required_datasets,
        );

    if (required) {

        return required;
    }

    if (
        isResolved(
            insight,
        )
    ) {

        return "Closed after current evidence";
    }

    return "Decision-ready evidence";
}


function rowRank(
    insight:
        BusinessPriority,
): number {

    if (
        isResolved(
            insight,
        )
    ) {

        return 4;
    }

    if (
        insight.type ===
            "risk"
        &&
        !isBlocked(
            insight,
        )
    ) {

        return 0;
    }

    if (
        insight.type ===
            "risk"
        &&
        isBlocked(
            insight,
        )
    ) {

        return 1;
    }

    if (
        insight.type ===
            "opportunity"
        &&
        !isBlocked(
            insight,
        )
    ) {

        return 2;
    }

    return 3;
}


// ============================================================
// PAGE
// ============================================================

export default async function PrioritiesPage() {

    const data =
        await getPriorities(
            true,
        );

    const insights = (
        data?.results
        ??
        []
    )
        .slice()
        .sort(
            (
                left,
                right,
            ) => {

                const rankDifference =
                    rowRank(
                        left,
                    )
                    -
                    rowRank(
                        right,
                    );

                if (
                    rankDifference !==
                    0
                ) {

                    return rankDifference;
                }

                return (
                    right
                        .priority_score
                    -
                    left
                        .priority_score
                );
            },
        );


    const currentRisks =
        insights.filter(
            (
                insight,
            ) => (
                insight.type ===
                    "risk"
                &&
                !isResolved(
                    insight,
                )
                &&
                !isBlocked(
                    insight,
                )
            ),
        );


    const blockedRisks =
        insights.filter(
            (
                insight,
            ) => (
                insight.type ===
                    "risk"
                &&
                isBlocked(
                    insight,
                )
            ),
        );


    const currentOpportunities =
        insights.filter(
            (
                insight,
            ) => (
                insight.type ===
                    "opportunity"
                &&
                !isResolved(
                    insight,
                )
                &&
                !isBlocked(
                    insight,
                )
            ),
        );


    const resolvedCount =
        insights.filter(
            isResolved,
        )
        .length;


    return (

        <main className="app-shell">

            <header className="page-header">

                <span className="section-kicker">
                    PRIORITY CENTER
                </span>

                <h1>
                    Business issues & opportunities
                </h1>

                <p>
                    Separate current management signals from prior
                    issues that remain open because required evidence
                    has not yet caught up.
                </p>

            </header>


            <section className="priority-summary-grid">

                <article>

                    <span>
                        Current risks
                    </span>

                    <strong>
                        {
                            currentRisks
                                .length
                        }
                    </strong>

                    <small>
                        Actionable in the current analytical cycle
                    </small>

                </article>


                <article>

                    <span>
                        Awaiting evidence
                    </span>

                    <strong>
                        {
                            blockedRisks
                                .length
                        }
                    </strong>

                    <small>
                        Kept open until required data becomes current
                    </small>

                </article>


                <article>

                    <span>
                        Opportunities
                    </span>

                    <strong>
                        {
                            currentOpportunities
                                .length
                        }
                    </strong>

                    <small>
                        Current positive signals worth evaluating
                    </small>

                </article>


                <article>

                    <span>
                        Resolved
                    </span>

                    <strong>
                        {
                            resolvedCount
                        }
                    </strong>

                    <small>
                        Closed after sufficient resolution evidence
                    </small>

                </article>

            </section>


            <div className="priority-table priority-table-v2">

                <div className="priority-table-header priority-table-header-v2">

                    <span>
                        Status
                    </span>

                    <span>
                        Insight
                    </span>

                    <span>
                        Evidence
                    </span>

                    <span>
                        Severity
                    </span>

                    <span>
                        Change
                    </span>

                    <span>
                        Next step
                    </span>

                </div>


                {
                    insights.map(
                        (
                            insight,
                        ) => (

                            <div
                                className="priority-table-row priority-table-row-v2"
                                key={
                                    insight
                                        .insight_id
                                    ??
                                    insight
                                        .fingerprint
                                }
                            >

                                <div>

                                    <span
                                        className={
                                            `lifecycle-badge lifecycle-${
                                                (
                                                    insight.lifecycle_status
                                                    ??
                                                    "NEW"
                                                )
                                                .toLowerCase()
                                            }`
                                        }
                                    >
                                        {
                                            insight
                                                .lifecycle_status
                                            ??
                                            "NEW"
                                        }
                                    </span>

                                </div>


                                <div className="priority-insight-cell">

                                    <strong>
                                        {
                                            insight
                                                .title
                                        }
                                    </strong>

                                    <small>
                                        {
                                            humanize(
                                                insight
                                                    .type,
                                            )
                                        }
                                        {" · "}
                                        {
                                            insight
                                                .entity
                                        }
                                    </small>

                                </div>


                                <div className="priority-evidence-cell">

                                    <span
                                        className={
                                            evidenceClass(
                                                insight,
                                            )
                                        }
                                    >
                                        {
                                            evidenceLabel(
                                                insight,
                                            )
                                        }
                                    </span>

                                    <small>
                                        {
                                            evidenceDetail(
                                                insight,
                                            )
                                        }
                                    </small>

                                </div>


                                <span>
                                    {
                                        humanize(
                                            insight
                                                .severity,
                                        )
                                    }
                                </span>


                                <strong>
                                    {
                                        insight
                                            .primary_change
                                    }
                                </strong>


                                {
                                    insight
                                        .insight_id
                                    ?
                                    (
                                        <Link
                                            href={
                                                `/investigate/${insight.insight_id}`
                                            }
                                        >
                                            Investigate →
                                        </Link>
                                    )
                                    :
                                    <span />
                                }

                            </div>
                        ),
                    )
                }

            </div>

        </main>
    );
}