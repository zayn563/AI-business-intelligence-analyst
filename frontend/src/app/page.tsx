import DashboardClient from "@/components/dashboard-client";

import {
    getDashboardData,
} from "@/lib/backend";


// ============================================================
// PAGE
// ============================================================

export default async function Home() {

    const dashboardData =
        await getDashboardData();

    return (
        <DashboardClient
            initialData={dashboardData}
        />
    );
}