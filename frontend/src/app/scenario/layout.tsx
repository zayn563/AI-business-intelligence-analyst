// ============================================================
// SCENARIO LAB ROUTE CONFIGURATION
// ============================================================
//
// Scenario Lab uses live business baselines from FastAPI.
//
// The route must remain dynamic so scenario context always
// reflects the current PostgreSQL data.
// ============================================================


export const dynamic =
    "force-dynamic";


export const revalidate =
    0;


// ============================================================
// LAYOUT
// ============================================================

export default function ScenarioLayout(
    {
        children,
    }: Readonly<{
        children:
            React.ReactNode;
    }>,
) {

    return children;
}