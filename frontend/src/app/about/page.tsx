export default function AboutPage() {

    return (

        <main className="app-shell">

            <header className="page-header">

                <span className="section-kicker">
                    PROJECT CASE STUDY
                </span>

                <h1>
                    From business data to decisions
                </h1>

                <p>
                    An end-to-end decision-intelligence platform built to detect, explain and prioritize meaningful commercial changes.
                </p>

            </header>


            <section className="case-study-grid">

                <article>

                    <span>
                        01
                    </span>

                    <h2>
                        Connect
                    </h2>

                    <p>
                        Live commercial data is ingested, validated, semantically mapped and stored in PostgreSQL.
                    </p>

                </article>


                <article>

                    <span>
                        02
                    </span>

                    <h2>
                        Detect
                    </h2>

                    <p>
                        Deterministic analytics automatically identify material KPI changes across business dimensions.
                    </p>

                </article>


                <article>

                    <span>
                        03
                    </span>

                    <h2>
                        Diagnose
                    </h2>

                    <p>
                        Supporting metrics are evaluated to identify likely volume, pricing, cost, discount and availability drivers.
                    </p>

                </article>


                <article>

                    <span>
                        04
                    </span>

                    <h2>
                        Prioritize
                    </h2>

                    <p>
                        Related signals are consolidated into management risks and growth opportunities.
                    </p>

                </article>


                <article>

                    <span>
                        05
                    </span>

                    <h2>
                        Recommend
                    </h2>

                    <p>
                        Evidence-backed action rules recommend the next investigation or management response.
                    </p>

                </article>


                <article>

                    <span>
                        06
                    </span>

                    <h2>
                        Decide
                    </h2>

                    <p>
                        Scenario modelling helps users test potential commercial responses before taking action.
                    </p>

                </article>

            </section>


            <section className="architecture-panel">

                <span className="section-kicker">
                    ARCHITECTURE
                </span>

                <h2>
                    Built as a complete analytical system
                </h2>


                <div className="architecture-flow">

                    <span>
                        Live source
                    </span>

                    <b>→</b>

                    <span>
                        Semantic layer
                    </span>

                    <b>→</b>

                    <span>
                        PostgreSQL
                    </span>

                    <b>→</b>

                    <span>
                        Deterministic intelligence
                    </span>

                    <b>→</b>

                    <span>
                        Priority engine
                    </span>

                    <b>→</b>

                    <span>
                        Decision interface
                    </span>

                </div>

            </section>

        </main>
    );
}