import Link
from "next/link";

import {
    getPriorities,
} from "@/lib/backend";


// ============================================================
// PAGE
// ============================================================

export default async function PrioritiesPage() {

    const data =
        await getPriorities(
            true,
        );


    const insights =
        data?.results
        ??
        [];


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
                    Track what is new, ongoing, escalating or resolved.
                </p>

            </header>


            <div className="priority-table">

                <div className="priority-table-header">

                    <span>
                        Status
                    </span>

                    <span>
                        Insight
                    </span>

                    <span>
                        Type
                    </span>

                    <span>
                        Severity
                    </span>

                    <span>
                        Change
                    </span>

                    <span>
                    </span>

                </div>


                {
                    insights.map(
                        (
                            insight,
                        ) => (

                            <div
                                className="priority-table-row"
                                key={
                                    insight.insight_id
                                    ??
                                    insight.fingerprint
                                }
                            >

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
                                        insight.lifecycle_status
                                        ??
                                        "NEW"
                                    }
                                </span>


                                <div>

                                    <strong>
                                        {insight.title}
                                    </strong>

                                    <small>
                                        {insight.entity}
                                    </small>

                                </div>


                                <span>
                                    {insight.type}
                                </span>


                                <span>
                                    {insight.severity}
                                </span>


                                <strong>
                                    {
                                        insight.primary_change
                                    }
                                </strong>


                                {
                                    insight.insight_id
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