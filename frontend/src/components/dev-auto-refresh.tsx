"use client";

import {
    useEffect,
    useRef,
} from "react";


// ============================================================
// CONFIGURATION
// ============================================================

/*
 * Healthy backend checks are intentionally infrequent.
 *
 * The previous implementation checked every 750 ms forever,
 * producing a large amount of unnecessary Next.js/FastAPI
 * traffic.
 */
const HEALTHY_CHECK_INTERVAL_MS =
    5000;


/*
 * If the backend disappears after previously being healthy,
 * retry more frequently so that Uvicorn recovery is detected
 * quickly during development.
 */
const UNHEALTHY_RETRY_INTERVAL_MS =
    1000;


// ============================================================
// RESPONSE
// ============================================================

type BackendHealthResponse = {

    healthy:
        boolean;

    status:
        number | null;
};


// ============================================================
// COMPONENT
// ============================================================

export default function DevAutoRefresh() {

    const backendWasHealthy =
        useRef(
            false,
        );


    const backendWentDown =
        useRef(
            false,
        );


    const reloadTriggered =
        useRef(
            false,
        );


    // ========================================================
    // DEVELOPMENT BACKEND RESTART DETECTION
    // ========================================================

    useEffect(
        () => {

            /*
             * Backend restart detection is a local-development
             * convenience only.
             */
            if (
                process.env.NODE_ENV
                !==
                "development"
            ) {

                return;
            }


            let disposed =
                false;


            let timer:
                number | null =
                    null;


            let requestInFlight =
                false;


            // ------------------------------------------------
            // SCHEDULE NEXT CHECK
            // ------------------------------------------------

            function scheduleNextCheck(
                delayMs:
                    number,
            ) {

                if (
                    disposed
                    ||
                    reloadTriggered.current
                ) {

                    return;
                }


                if (
                    timer
                    !==
                    null
                ) {

                    window.clearTimeout(
                        timer,
                    );
                }


                timer =
                    window.setTimeout(
                        () => {

                            timer =
                                null;


                            void checkBackend();

                        },
                        delayMs,
                    );
            }


            // ------------------------------------------------
            // CHECK BACKEND
            // ------------------------------------------------

            async function checkBackend() {

                if (
                    disposed
                    ||
                    reloadTriggered.current
                    ||
                    requestInFlight
                ) {

                    return;
                }


                requestInFlight =
                    true;


                let nextDelay =
                    HEALTHY_CHECK_INTERVAL_MS;


                try {

                    const response =
                        await fetch(
                            "/api/dev/backend-health",
                            {
                                method:
                                    "GET",

                                cache:
                                    "no-store",
                            },
                        );


                    if (
                        !response.ok
                    ) {

                        if (
                            backendWasHealthy.current
                        ) {

                            backendWentDown.current =
                                true;
                        }


                        nextDelay =
                            UNHEALTHY_RETRY_INTERVAL_MS;


                        return;
                    }


                    const payload = (
                        await response.json()
                    ) as BackendHealthResponse;


                    // ----------------------------------------
                    // BACKEND CURRENTLY HEALTHY
                    // ----------------------------------------

                    if (
                        payload.healthy
                    ) {

                        /*
                         * Backend was healthy, disappeared,
                         * and has now recovered.
                         *
                         * This usually means Uvicorn completed
                         * an automatic development reload.
                         */
                        if (
                            backendWasHealthy.current
                            &&
                            backendWentDown.current
                        ) {

                            reloadTriggered.current =
                                true;


                            window.location.reload();


                            return;
                        }


                        backendWasHealthy.current =
                            true;


                        backendWentDown.current =
                            false;


                        nextDelay =
                            HEALTHY_CHECK_INTERVAL_MS;


                        return;
                    }


                    // ----------------------------------------
                    // BACKEND CURRENTLY UNAVAILABLE
                    // ----------------------------------------

                    if (
                        backendWasHealthy.current
                    ) {

                        backendWentDown.current =
                            true;
                    }


                    nextDelay =
                        UNHEALTHY_RETRY_INTERVAL_MS;

                }
                catch {

                    if (
                        backendWasHealthy.current
                    ) {

                        backendWentDown.current =
                            true;
                    }


                    nextDelay =
                        UNHEALTHY_RETRY_INTERVAL_MS;
                }
                finally {

                    requestInFlight =
                        false;


                    if (
                        !disposed
                        &&
                        !reloadTriggered.current
                    ) {

                        scheduleNextCheck(
                            nextDelay,
                        );
                    }
                }
            }


            // ------------------------------------------------
            // INITIAL CHECK
            // ------------------------------------------------

            /*
             * Check immediately once when the component mounts.
             *
             * Further checks use recursive setTimeout rather
             * than setInterval so requests can never overlap.
             */
            void checkBackend();


            // ------------------------------------------------
            // CLEANUP
            // ------------------------------------------------

            return () => {

                disposed =
                    true;


                if (
                    timer
                    !==
                    null
                ) {

                    window.clearTimeout(
                        timer,
                    );
                }
            };

        },
        [],
    );


    // ========================================================
    // UI
    // ========================================================

    return null;
}