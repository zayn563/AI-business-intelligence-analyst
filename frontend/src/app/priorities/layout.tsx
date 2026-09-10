// ============================================================
// PRIORITIES ROUTE CONFIGURATION
// ============================================================
//
// Priorities are backed by live FastAPI / PostgreSQL data.
//
// This route must never be statically prerendered during the
// Next.js production build.
// ============================================================


export const dynamic =
    "force-dynamic";


export const revalidate =
    0;


// ============================================================
// LAYOUT
// ============================================================

export default function PrioritiesLayout(
    {
        children,
    }: Readonly<{
        children:
            React.ReactNode;
    }>,
) {

    return children;
}