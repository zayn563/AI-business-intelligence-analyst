// ============================================================
// DATA WORKSPACE ROUTE CONFIGURATION
// ============================================================
//
// The Data workspace displays live pipeline and background-job
// information from FastAPI / PostgreSQL.
//
// It must be rendered dynamically.
// ============================================================


export const dynamic =
    "force-dynamic";


export const revalidate =
    0;


// ============================================================
// LAYOUT
// ============================================================

export default function DataLayout(
    {
        children,
    }: Readonly<{
        children:
            React.ReactNode;
    }>,
) {

    return children;
}