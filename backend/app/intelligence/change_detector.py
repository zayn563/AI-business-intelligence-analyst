from .thresholds import (
    METRIC_RULES,
)


# ============================================================
# HELPERS
# ============================================================

def percentage_change(
    current: float,
    previous: float,
) -> float | None:

    if previous == 0:

        return None

    return (
        (
            current
            -
            previous
        )
        /
        abs(previous)
        *
        100.0
    )


def classify_severity(
    metric: str,
    magnitude: float,
) -> str:

    rule = (
        METRIC_RULES[
            metric
        ]
    )

    if (
        magnitude
        >=
        rule["high"]
    ):

        return "high"

    if (
        magnitude
        >=
        rule["medium"]
    ):

        return "medium"

    if (
        magnitude
        >=
        rule["low"]
    ):

        return "low"

    return "informational"


def classify_impact(
    metric: str,
    direction: str,
) -> str:

    rule = (
        METRIC_RULES[
            metric
        ]
    )

    preference = (
        rule[
            "preferred"
        ]
    )

    if (
        direction
        ==
        "flat"
    ):

        return "neutral"

    if (
        preference
        ==
        "neutral"
    ):

        return "contextual"

    if (
        preference
        ==
        "higher"
    ):

        return (
            "positive"
            if direction
            ==
            "increase"
            else
            "negative"
        )

    if (
        preference
        ==
        "lower"
    ):

        return (
            "positive"
            if direction
            ==
            "decrease"
            else
            "negative"
        )

    return "neutral"


# ============================================================
# BUILD CHANGE EVENT
# ============================================================

def build_change_event(
    metric: str,
    dimension: str,
    dimension_value: str,
    current_value: float,
    previous_value: float,
) -> dict | None:

    if (
        current_value
        is None
        or
        previous_value
        is None
    ):

        return None

    if (
        metric
        not in
        METRIC_RULES
    ):

        raise ValueError(
            f"Unsupported metric: {metric}"
        )

    rule = (
        METRIC_RULES[
            metric
        ]
    )

    absolute_change = (
        current_value
        -
        previous_value
    )

    if absolute_change > 0:

        direction = (
            "increase"
        )

    elif absolute_change < 0:

        direction = (
            "decrease"
        )

    else:

        direction = (
            "flat"
        )

    if (
        rule["mode"]
        ==
        "pp"
    ):

        change_pp = (
            absolute_change
        )

        change_pct = (
            percentage_change(
                current_value,
                previous_value,
            )
        )

        magnitude = abs(
            change_pp
        )

    else:

        change_pct = (
            percentage_change(
                current_value,
                previous_value,
            )
        )

        change_pp = None

        if (
            change_pct
            is None
        ):

            magnitude = 0.0

        else:

            magnitude = abs(
                change_pct
            )

    severity = (
        classify_severity(
            metric,
            magnitude,
        )
    )

    return {
        "metric":
            metric,

        "dimension":
            dimension,

        "dimension_value":
            dimension_value,

        "current_value":
            round(
                float(
                    current_value
                ),
                4,
            ),

        "previous_value":
            round(
                float(
                    previous_value
                ),
                4,
            ),

        "absolute_change":
            round(
                float(
                    absolute_change
                ),
                4,
            ),

        "change_pct":
            (
                None
                if
                change_pct
                is None
                else
                round(
                    float(
                        change_pct
                    ),
                    2,
                )
            ),

        "change_pp":
            (
                None
                if
                change_pp
                is None
                else
                round(
                    float(
                        change_pp
                    ),
                    2,
                )
            ),

        "direction":
            direction,

        "severity":
            severity,

        "material":
            (
                severity
                !=
                "informational"
            ),

        "impact":
            classify_impact(
                metric,
                direction,
            ),
    }


# ============================================================
# COMPARE SNAPSHOTS
# ============================================================

def compare_snapshots(
    current_snapshot: dict,
    previous_snapshot: dict,
    dimension: str,
    metrics: list[str],
) -> list[dict]:

    events = []

    common_entities = (
        set(
            current_snapshot.keys()
        )
        &
        set(
            previous_snapshot.keys()
        )
    )

    for entity in (
        sorted(
            common_entities
        )
    ):

        current = (
            current_snapshot[
                entity
            ]
        )

        previous = (
            previous_snapshot[
                entity
            ]
        )

        for metric in metrics:

            if (
                metric
                not in current
                or
                metric
                not in previous
            ):

                continue

            event = (
                build_change_event(
                    metric=
                        metric,

                    dimension=
                        dimension,

                    dimension_value=
                        entity,

                    current_value=
                        current.get(
                            metric
                        ),

                    previous_value=
                        previous.get(
                            metric
                        ),
                )
            )

            if event is not None:

                events.append(
                    event
                )

    return events