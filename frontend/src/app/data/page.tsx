import DataCenter
from "@/components/data-center";

import {
    getDataStatus,
} from "@/lib/backend";


// ============================================================
// PAGE
// ============================================================

export default async function DataPage() {

    const status =
        await getDataStatus();


    return (

        <main className="app-shell">

            <header className="page-header">

                <span className="section-kicker">
                    DATA WORKSPACE
                </span>

                <h1>
                    Connected business data
                </h1>

                <p>
                    Review data freshness and refresh the sources feeding the intelligence platform.
                </p>

            </header>


            <DataCenter
                status={
                    status
                }
            />

        </main>
    );
}