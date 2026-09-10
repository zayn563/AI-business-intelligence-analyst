import Link
from "next/link";

import ThemeToggle
from "@/components/theme-toggle";


export default function SiteNav() {

    return (

        <nav className="site-nav">

            <div className="site-nav-inner">

                <Link
                    href="/"
                    className="brand-link"
                >

                    <span className="brand-mark">
                        AI BI
                    </span>

                    <span className="brand-subtitle">
                        Analyst
                    </span>

                </Link>


                <div className="nav-right">

                    <div className="nav-links">

                        <Link href="/">
                            Overview
                        </Link>

                        <Link href="/priorities">
                            Priorities
                        </Link>

                        <Link href="/scenario">
                            Scenario Lab
                        </Link>

                        <Link href="/data">
                            Data
                        </Link>

                        <Link href="/about">
                            Project
                        </Link>

                    </div>


                    <ThemeToggle />

                </div>

            </div>

        </nav>
    );
}