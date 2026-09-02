// ============================================================
// INVESTIGATION ROUTE CONFIGURATION
// ============================================================
//
// Investigation pages depend on persisted live insights,
// actions and drill-down diagnostics.
//
// They must never be statically prerendered.
// ============================================================


export const dynamic =
    "force-dynamic";


export const revalidate =
    0;


// ============================================================
// LAYOUT
// ============================================================

export default function InvestigationLayout(
    {
        children,
    }: Readonly<{
        children:
            React.ReactNode;
    }>,
) {

    return children;
}