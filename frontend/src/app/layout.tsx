import type {
    Metadata,
} from "next";

import type {
    ReactNode,
} from "react";

import DevAutoRefresh
    from "@/components/dev-auto-refresh";

import SiteNav
    from "@/components/site-nav";

import "./globals.css";
import "./theme-overrides.css";
import "./job-ui.css";
import "./action-panel.css";
import "./iteration-2.css";
import "./accessibility-overrides.css";


/*
 * This application is backed by live PostgreSQL/FastAPI data.
 *
 * The dashboard, priorities, scenario workspace and operational
 * pages should therefore be rendered dynamically rather than
 * being statically prerendered during `next build`.
 *
 * This also prevents Next.js from treating our `no-store` /
 * `revalidate: 0` backend requests as static-render bailouts
 * during the production build.
 */
export const dynamic =
    "force-dynamic";

export const revalidate =
    0;


export const metadata:
    Metadata = {

    title:
        "AI Business Intelligence Analyst",

    description:
        (
            "Evidence-grounded decision-intelligence "
            +
            "platform for monitoring commercial performance, "
            +
            "prioritizing material change, investigating "
            +
            "business drivers and supporting management action."
        ),
};


const themeBootstrap = `
(function () {
    try {
        var stored =
            localStorage.getItem(
                "aibi-theme"
            ) || "system";

        var resolved =
            stored;

        if (stored === "system") {
            resolved =
                window.matchMedia(
                    "(prefers-color-scheme: dark)"
                ).matches
                    ? "dark"
                    : "light";
        }

        document.documentElement.dataset.theme =
            resolved;

        document.documentElement.dataset.themePreference =
            stored;

        document.documentElement.style.colorScheme =
            resolved;
    } catch (error) {
        document.documentElement.dataset.theme =
            "light";

        document.documentElement.dataset.themePreference =
            "system";

        document.documentElement.style.colorScheme =
            "light";
    }
})();
`;


interface RootLayoutProps {

    children:
        ReactNode;
}


export default function RootLayout(
    {
        children,
    }: Readonly<RootLayoutProps>,
) {

    return (

        <html
            lang="en"
            suppressHydrationWarning
        >

            <head>

                <script
                    dangerouslySetInnerHTML={{
                        __html:
                            themeBootstrap,
                    }}
                />

            </head>


            <body>

                <SiteNav />

                {children}

                <DevAutoRefresh />

            </body>

        </html>
    );
}