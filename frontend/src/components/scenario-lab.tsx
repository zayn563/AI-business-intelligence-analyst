"use client";


import {
    ChangeEvent,
    useEffect,
    useRef,
    useState,
} from "react";


import styles
    from "./scenario-lab.module.css";


type ScenarioDimension =
    "overall" |
    "region";


interface ScenarioScope {
    key: string;
    label: string;
    dimension: ScenarioDimension;
    value: string | null;
}


interface Period {
    start: string;
    end: string;
}


interface ScenarioConfiguration {
    status: "success";
    data_through: string;
    baseline_period: Period;
    comparison_period: Period;
    calculation_basis: string;
    scopes: ScenarioScope[];
}


interface LeverState {
    volume_change_pct: number;
    list_price_change_pct: number;
    discount_rate_change_pp: number;
    cost_per_unit_change_pct: number;
}


interface Metrics {
    net_sales: number;
    gross_profit: number;
    margin_pct: number;
    units_sold: number;
    discount_pct: number;
    cost_per_unit: number;
}


interface ScenarioMetrics
    extends Metrics {

    gross_sales: number;
    cogs: number;
}


interface ScenarioResponse {
    status: "success";

    scope: ScenarioScope;

    data_through: string;

    baseline_period: Period;

    comparison_period: Period;

    calculation_basis: string;

    baseline: Metrics;

    levers: LeverState;

    scenario: ScenarioMetrics;

    delta: {
        net_sales: number;
        gross_profit: number;
        margin_pp: number;
        units_sold: number;
    };
}


interface ErrorResponse {
    status?: string;
    detail?: string;
}


const ZERO_LEVERS:
    LeverState = {

    volume_change_pct:
        0,

    list_price_change_pct:
        0,

    discount_rate_change_pp:
        0,

    cost_per_unit_change_pct:
        0,
};


function formatDate(
    value: string,
): string {

    const date =
        new Date(
            `${value}T00:00:00`,
        );


    return new Intl
        .DateTimeFormat(
            "en-US",
            {
                month:
                    "short",

                day:
                    "numeric",

                year:
                    "numeric",
            },
        )
        .format(
            date,
        );
}


function formatPeriod(
    period: Period,
): string {

    return (
        `${formatDate(period.start)}`
        +
        " — "
        +
        `${formatDate(period.end)}`
    );
}


function formatCompactNumber(
    value: number,
): string {

    const absolute =
        Math.abs(
            value,
        );


    if (
        absolute >=
        1_000_000
    ) {

        return (
            `${(
                value /
                1_000_000
            ).toFixed(2)}M`
        );
    }


    if (
        absolute >=
        1_000
    ) {

        return (
            `${(
                value /
                1_000
            ).toFixed(1)}K`
        );
    }


    return value
        .toFixed(
            2,
        );
}


function formatUnits(
    value: number,
): string {

    const absolute =
        Math.abs(
            value,
        );


    if (
        absolute >=
        1_000_000
    ) {

        return (
            `${(
                value /
                1_000_000
            ).toFixed(2)}M`
        );
    }


    if (
        absolute >=
        1_000
    ) {

        return (
            `${(
                value /
                1_000
            ).toFixed(1)}K`
        );
    }


    return Math.round(
        value,
    ).toLocaleString(
        "en-US",
    );
}


function formatPercent(
    value: number,
): string {

    return (
        `${value.toFixed(1)}%`
    );
}


function formatMoneyPerUnit(
    value: number,
): string {

    return value
        .toFixed(
            2,
        );
}


function formatDelta(
    value: number,
    suffix = "",
): string {

    const rounded =
        Math.abs(
            value,
        ) <
        0.005
            ? 0
            : value;


    const sign =
        rounded >
        0
            ? "+"
            : "";


    return (
        `${sign}${formatCompactNumber(rounded)}${suffix}`
    );
}


function formatPercentLever(
    value: number,
): string {

    const sign =
        value >
        0
            ? "+"
            : "";


    return (
        `${sign}${value}%`
    );
}


function formatPointLever(
    value: number,
): string {

    const sign =
        value >
        0
            ? "+"
            : "";


    return (
        `${sign}${value.toFixed(1)} pp`
    );
}


async function responseJson<T>(
    response: Response,
): Promise<T> {

    const payload =
        (
            await response.json()
        ) as T &
            ErrorResponse;


    if (
        !response.ok
    ) {

        throw new Error(
            payload.detail ??
            (
                "The scenario service "
                +
                "returned an error."
            ),
        );
    }


    return payload;
}


async function loadConfiguration():
    Promise<ScenarioConfiguration> {

    const response =
        await fetch(
            "/api/scenario",
            {
                method:
                    "GET",

                cache:
                    "no-store",
            },
        );


    return responseJson<
        ScenarioConfiguration
    >(
        response,
    );
}


async function calculateScenario(
    scope: ScenarioScope,
    levers: LeverState,
): Promise<ScenarioResponse> {

    const response =
        await fetch(
            "/api/scenario",
            {
                method:
                    "POST",

                headers: {
                    "Content-Type":
                        "application/json",
                },

                cache:
                    "no-store",

                body:
                    JSON.stringify(
                        {
                            scope: {
                                dimension:
                                    scope.dimension,

                                value:
                                    scope.value,
                            },

                            ...levers,
                        },
                    ),
            },
        );


    return responseJson<
        ScenarioResponse
    >(
        response,
    );
}


interface SliderProps {
    label: string;
    value: number;
    minimum: number;
    maximum: number;
    step: number;
    displayValue: string;
    disabled: boolean;
    onChange:
        (
            value: number,
        ) => void;
}


function ScenarioSlider(
    {
        label,
        value,
        minimum,
        maximum,
        step,
        displayValue,
        disabled,
        onChange,
    }: SliderProps,
) {

    function handleChange(
        event:
            ChangeEvent<HTMLInputElement>,
    ) {

        onChange(
            Number(
                event.target.value,
            ),
        );
    }


    return (
        <div
            className={
                styles.sliderGroup
            }
        >
            <div
                className={
                    styles.sliderHeader
                }
            >
                <label>
                    {label}
                </label>

                <strong>
                    {displayValue}
                </strong>
            </div>

            <input
                aria-label={label}
                className={
                    styles.slider
                }
                disabled={
                    disabled
                }
                max={
                    maximum
                }
                min={
                    minimum
                }
                onChange={
                    handleChange
                }
                step={
                    step
                }
                type="range"
                value={
                    value
                }
            />
        </div>
    );
}


export default function ScenarioLab() {

    const [
        configuration,
        setConfiguration,
    ] =
        useState<
            ScenarioConfiguration |
            null
        >(
            null,
        );


    const [
        selectedScopeKey,
        setSelectedScopeKey,
    ] =
        useState(
            "overall",
        );


    const [
        levers,
        setLevers,
    ] =
        useState<
            LeverState
        >(
            ZERO_LEVERS,
        );


    const [
        result,
        setResult,
    ] =
        useState<
            ScenarioResponse |
            null
        >(
            null,
        );


    const [
        loading,
        setLoading,
    ] =
        useState(
            true,
        );


    const [
        calculating,
        setCalculating,
    ] =
        useState(
            false,
        );


    const [
        error,
        setError,
    ] =
        useState<
            string |
            null
        >(
            null,
        );


    const requestIdRef =
        useRef(
            0,
        );


    useEffect(
        () => {

            let active =
                true;


            async function initialize() {

                try {

                    const config =
                        await loadConfiguration();


                    if (
                        !active
                    ) {

                        return;
                    }


                    const overall =
                        config.scopes.find(
                            (
                                scope,
                            ) =>
                                scope.key ===
                                "overall",
                        )
                        ??
                        config.scopes[
                            0
                        ];


                    if (
                        !overall
                    ) {

                        throw new Error(
                            (
                                "No scenario "
                                +
                                "scope is available."
                            ),
                        );
                    }


                    const initial =
                        await calculateScenario(
                            overall,
                            ZERO_LEVERS,
                        );


                    if (
                        !active
                    ) {

                        return;
                    }


                    setConfiguration(
                        config,
                    );

                    setSelectedScopeKey(
                        overall.key,
                    );

                    setResult(
                        initial,
                    );

                    setError(
                        null,
                    );

                } catch (
                    caught
                ) {

                    if (
                        active
                    ) {

                        setError(
                            caught instanceof
                            Error
                                ? caught.message
                                : (
                                    "Scenario Lab "
                                    +
                                    "could not be loaded."
                                ),
                        );
                    }

                } finally {

                    if (
                        active
                    ) {

                        setLoading(
                            false,
                        );
                    }
                }
            }


            void initialize();


            return () => {

                active =
                    false;
            };
        },
        [],
    );


    const selectedScope =
        configuration
            ?.scopes
            .find(
                (
                    scope,
                ) =>
                    scope.key ===
                    selectedScopeKey,
            )
        ??
        result?.scope
        ??
        null;


    async function requestCalculation(
        scope: ScenarioScope,
        nextLevers: LeverState,
    ) {

        const requestId =
            requestIdRef.current +
            1;


        requestIdRef.current =
            requestId;


        setCalculating(
            true,
        );

        setError(
            null,
        );


        try {

            const nextResult =
                await calculateScenario(
                    scope,
                    nextLevers,
                );


            if (
                requestId !==
                requestIdRef.current
            ) {

                return;
            }


            setResult(
                nextResult,
            );

        } catch (
            caught
        ) {

            if (
                requestId ===
                requestIdRef.current
            ) {

                setError(
                    caught instanceof
                    Error
                        ? caught.message
                        : (
                            "Scenario calculation "
                            +
                            "failed."
                        ),
                );
            }

        } finally {

            if (
                requestId ===
                requestIdRef.current
            ) {

                setCalculating(
                    false,
                );
            }
        }
    }


    async function handleScopeChange(
        event:
            ChangeEvent<HTMLSelectElement>,
    ) {

        if (
            !configuration
        ) {

            return;
        }


        const nextScope =
            configuration.scopes.find(
                (
                    scope,
                ) =>
                    scope.key ===
                    event.target.value,
            );


        if (
            !nextScope
        ) {

            return;
        }


        setSelectedScopeKey(
            nextScope.key,
        );


        const nextLevers = {
            ...ZERO_LEVERS,
        };


        setLevers(
            nextLevers,
        );


        await requestCalculation(
            nextScope,
            nextLevers,
        );
    }


    function updateLever(
        field:
            keyof LeverState,
        value: number,
    ) {

        setLevers(
            (
                current,
            ) => (
                {
                    ...current,

                    [field]:
                        value,
                }
            ),
        );
    }


    async function handleCalculate() {

        if (
            !selectedScope
        ) {

            return;
        }


        await requestCalculation(
            selectedScope,
            levers,
        );
    }


    async function handleReset() {

        if (
            !selectedScope
        ) {

            return;
        }


        const nextLevers = {
            ...ZERO_LEVERS,
        };


        setLevers(
            nextLevers,
        );


        await requestCalculation(
            selectedScope,
            nextLevers,
        );
    }


    if (
        loading
    ) {

        return (
            <main
                className={
                    styles.root
                }
            >
                <section
                    className={
                        styles.loadingPanel
                    }
                >
                    Loading the latest
                    deterministic business
                    baseline...
                </section>
            </main>
        );
    }


    if (
        !configuration
        ||
        !selectedScope
        ||
        !result
    ) {

        return (
            <main
                className={
                    styles.root
                }
            >
                <section
                    className={
                        styles.errorPanel
                    }
                >
                    <strong>
                        Scenario Lab could not
                        be loaded.
                    </strong>

                    <p>
                        {
                            error ??
                            (
                                "The deterministic "
                                +
                                "analytics service "
                                +
                                "did not return a "
                                +
                                "usable baseline."
                            )
                        }
                    </p>
                </section>
            </main>
        );
    }


    return (
        <main
            className={
                styles.root
            }
        >
            <section
                className={
                    styles.hero
                }
            >
                <p
                    className={
                        styles.eyebrow
                    }
                >
                    Scenario Lab
                </p>

                <h1>
                    Model a business
                    decision
                </h1>

                <p
                    className={
                        styles.heroCopy
                    }
                >
                    Test how changes in
                    volume, price, discounts
                    and cost could affect
                    commercial performance
                    before taking action.
                </p>
            </section>


            <section
                className={
                    styles.scopePanel
                }
            >
                <div
                    className={
                        styles.scopeSelector
                    }
                >
                    <label
                        htmlFor={
                            "scenario-scope"
                        }
                    >
                        Business scope
                    </label>

                    <select
                        id={
                            "scenario-scope"
                        }
                        onChange={
                            (
                                event,
                            ) => {
                                void handleScopeChange(
                                    event,
                                );
                            }
                        }
                        value={
                            selectedScopeKey
                        }
                    >
                        {
                            configuration
                                .scopes
                                .map(
                                    (
                                        scope,
                                    ) => (
                                        <option
                                            key={
                                                scope.key
                                            }
                                            value={
                                                scope.key
                                            }
                                        >
                                            {
                                                scope.label
                                            }
                                        </option>
                                    ),
                                )
                        }
                    </select>
                </div>


                <div
                    className={
                        styles.scopeSummary
                    }
                >
                    <p
                        className={
                            styles.eyebrow
                        }
                    >
                        You are modelling
                    </p>

                    <h2>
                        {
                            result
                                .scope
                                .label
                        }
                    </h2>

                    <p>
                        All baseline and
                        estimated values below
                        are isolated to this
                        selected business scope.
                    </p>
                </div>


                <div
                    className={
                        styles.contextGrid
                    }
                >
                    <div
                        className={
                            styles.contextCard
                        }
                    >
                        <span>
                            Baseline period
                        </span>

                        <strong>
                            {
                                formatPeriod(
                                    result
                                        .baseline_period,
                                )
                            }
                        </strong>
                    </div>

                    <div
                        className={
                            styles.contextCard
                        }
                    >
                        <span>
                            Data through
                        </span>

                        <strong>
                            {
                                formatDate(
                                    result
                                        .data_through,
                                )
                            }
                        </strong>
                    </div>

                    <div
                        className={
                            styles.contextCard
                        }
                    >
                        <span>
                            Calculation basis
                        </span>

                        <strong>
                            {
                                result
                                    .calculation_basis
                            }
                        </strong>
                    </div>
                </div>
            </section>


            {
                error
                    ? (
                        <section
                            className={
                                styles.errorBanner
                            }
                        >
                            {error}
                        </section>
                    )
                    : null
            }


            <section
                className={
                    styles.modelGrid
                }
            >
                <div
                    className={
                        styles.leverPanel
                    }
                >
                    <h2>
                        Business levers
                    </h2>


                    <ScenarioSlider
                        disabled={
                            calculating
                        }
                        displayValue={
                            formatPercentLever(
                                levers
                                    .volume_change_pct,
                            )
                        }
                        label={
                            "Volume change"
                        }
                        maximum={
                            30
                        }
                        minimum={
                            -30
                        }
                        onChange={
                            (
                                value,
                            ) =>
                                updateLever(
                                    "volume_change_pct",
                                    value,
                                )
                        }
                        step={
                            1
                        }
                        value={
                            levers
                                .volume_change_pct
                        }
                    />


                    <ScenarioSlider
                        disabled={
                            calculating
                        }
                        displayValue={
                            formatPercentLever(
                                levers
                                    .list_price_change_pct,
                            )
                        }
                        label={
                            "List price change"
                        }
                        maximum={
                            20
                        }
                        minimum={
                            -20
                        }
                        onChange={
                            (
                                value,
                            ) =>
                                updateLever(
                                    "list_price_change_pct",
                                    value,
                                )
                        }
                        step={
                            1
                        }
                        value={
                            levers
                                .list_price_change_pct
                        }
                    />


                    <ScenarioSlider
                        disabled={
                            calculating
                        }
                        displayValue={
                            formatPointLever(
                                levers
                                    .discount_rate_change_pp,
                            )
                        }
                        label={
                            "Discount rate change"
                        }
                        maximum={
                            20
                        }
                        minimum={
                            -15
                        }
                        onChange={
                            (
                                value,
                            ) =>
                                updateLever(
                                    "discount_rate_change_pp",
                                    value,
                                )
                        }
                        step={
                            0.5
                        }
                        value={
                            levers
                                .discount_rate_change_pp
                        }
                    />


                    <ScenarioSlider
                        disabled={
                            calculating
                        }
                        displayValue={
                            formatPercentLever(
                                levers
                                    .cost_per_unit_change_pct,
                            )
                        }
                        label={
                            "Cost per unit change"
                        }
                        maximum={
                            25
                        }
                        minimum={
                            -20
                        }
                        onChange={
                            (
                                value,
                            ) =>
                                updateLever(
                                    "cost_per_unit_change_pct",
                                    value,
                                )
                        }
                        step={
                            1
                        }
                        value={
                            levers
                                .cost_per_unit_change_pct
                        }
                    />


                    <div
                        className={
                            styles.buttonRow
                        }
                    >
                        <button
                            className={
                                styles.primaryButton
                            }
                            disabled={
                                calculating
                            }
                            onClick={
                                () => {
                                    void handleCalculate();
                                }
                            }
                            type="button"
                        >
                            {
                                calculating
                                    ? (
                                        "Calculating..."
                                    )
                                    : (
                                        `Calculate ${
                                            result.scope.dimension ===
                                            "region"
                                                ? result.scope.value
                                                : "overall"
                                        } scenario`
                                    )
                            }
                        </button>

                        <button
                            className={
                                styles.secondaryButton
                            }
                            disabled={
                                calculating
                            }
                            onClick={
                                () => {
                                    void handleReset();
                                }
                            }
                            type="button"
                        >
                            Reset
                        </button>
                    </div>
                </div>


                <div
                    className={
                        styles.resultPanel
                    }
                >
                    <p
                        className={
                            styles.eyebrow
                        }
                    >
                        Estimated scenario
                    </p>

                    <h2>
                        {
                            result
                                .scope
                                .label
                        }
                    </h2>


                    <div
                        className={
                            styles.resultGrid
                        }
                    >
                        <article
                            className={
                                styles.resultCard
                            }
                        >
                            <span>
                                Net sales
                            </span>

                            <strong>
                                {
                                    formatCompactNumber(
                                        result
                                            .scenario
                                            .net_sales,
                                    )
                                }
                            </strong>

                            <small>
                                Δ {
                                    formatDelta(
                                        result
                                            .delta
                                            .net_sales,
                                    )
                                }
                            </small>
                        </article>


                        <article
                            className={
                                styles.resultCard
                            }
                        >
                            <span>
                                Gross profit
                            </span>

                            <strong>
                                {
                                    formatCompactNumber(
                                        result
                                            .scenario
                                            .gross_profit,
                                    )
                                }
                            </strong>

                            <small>
                                Δ {
                                    formatDelta(
                                        result
                                            .delta
                                            .gross_profit,
                                    )
                                }
                            </small>
                        </article>


                        <article
                            className={
                                styles.resultCard
                            }
                        >
                            <span>
                                Gross margin
                            </span>

                            <strong>
                                {
                                    formatPercent(
                                        result
                                            .scenario
                                            .margin_pct,
                                    )
                                }
                            </strong>

                            <small>
                                Δ {
                                    result
                                        .delta
                                        .margin_pp
                                        .toFixed(
                                            1,
                                        )
                                } pp
                            </small>
                        </article>
                    </div>


                    <div
                        className={
                            styles.baselineTitle
                        }
                    >
                        Selected-scope actual
                        baseline
                    </div>


                    <div
                        className={
                            styles.baselineGrid
                        }
                    >
                        <div>
                            <span>
                                Baseline sales
                            </span>

                            <strong>
                                {
                                    formatCompactNumber(
                                        result
                                            .baseline
                                            .net_sales,
                                    )
                                }
                            </strong>
                        </div>

                        <div>
                            <span>
                                Baseline gross profit
                            </span>

                            <strong>
                                {
                                    formatCompactNumber(
                                        result
                                            .baseline
                                            .gross_profit,
                                    )
                                }
                            </strong>
                        </div>

                        <div>
                            <span>
                                Baseline margin
                            </span>

                            <strong>
                                {
                                    formatPercent(
                                        result
                                            .baseline
                                            .margin_pct,
                                    )
                                }
                            </strong>
                        </div>

                        <div>
                            <span>
                                Baseline units
                            </span>

                            <strong>
                                {
                                    formatUnits(
                                        result
                                            .baseline
                                            .units_sold,
                                    )
                                }
                            </strong>
                        </div>

                        <div>
                            <span>
                                Discount rate
                            </span>

                            <strong>
                                {
                                    formatPercent(
                                        result
                                            .baseline
                                            .discount_pct,
                                    )
                                }
                            </strong>
                        </div>

                        <div>
                            <span>
                                Cost per unit
                            </span>

                            <strong>
                                {
                                    formatMoneyPerUnit(
                                        result
                                            .baseline
                                            .cost_per_unit,
                                    )
                                }
                            </strong>
                        </div>
                    </div>


                    <p
                        className={
                            styles.disclaimer
                        }
                    >
                        Scenario estimates are
                        deterministic sensitivity
                        calculations based only
                        on the actual selected
                        scope baseline. They are
                        decision-support estimates,
                        not forecasts, and they do
                        not modify warehouse data
                        or other regions.
                    </p>
                </div>
            </section>
        </main>
    );
}