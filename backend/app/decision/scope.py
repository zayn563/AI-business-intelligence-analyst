from __future__ import annotations


# ============================================================
# PREFIXED IDS
# ============================================================

def prefixed_id(
    value: str,
) -> str | None:

    cleaned = (
        value
        .strip()
    )

    if "|" in cleaned:

        prefix = (
            cleaned
            .split(
                "|",
                1,
            )[
                0
            ]
            .strip()
        )

        if prefix:
            return prefix

    if cleaned.isdigit():
        return cleaned

    return None


# ============================================================
# SCOPE FILTER
# ============================================================

def scope_filter(
    dimension: str,
    value: str,
) -> tuple[
    str,
    dict,
]:

    dimension = (
        dimension
        .strip()
        .lower()
    )

    value = (
        value
        .strip()
    )


    if dimension == "overall":

        return (
            "1 = 1",
            {},
        )


    if dimension == "region":

        return (
            "s.region = :scope_value",
            {
                "scope_value":
                    value,
            },
        )


    if dimension == "city":

        return (
            "s.city = :scope_value",
            {
                "scope_value":
                    value,
            },
        )


    if dimension == "channel":

        return (
            "s.channel = :scope_value",
            {
                "scope_value":
                    value,
            },
        )


    if dimension == "category":

        return (
            "p.category = :scope_value",
            {
                "scope_value":
                    value,
            },
        )


    if dimension == "brand":

        return (
            "p.brand = :scope_value",
            {
                "scope_value":
                    value,
            },
        )


    if dimension == "product":

        product_id = (
            prefixed_id(
                value
            )
        )

        if product_id:

            return (
                "CAST(p.product_id AS TEXT) = :scope_id",
                {
                    "scope_id":
                        product_id,
                },
            )

        return (
            "p.product_name = :scope_value",
            {
                "scope_value":
                    value,
            },
        )


    if dimension == "store":

        store_id = (
            prefixed_id(
                value
            )
        )

        if store_id:

            return (
                "CAST(s.store_id AS TEXT) = :scope_id",
                {
                    "scope_id":
                        store_id,
                },
            )

        return (
            "s.store_name = :scope_value",
            {
                "scope_value":
                    value,
            },
        )


    if dimension == "salesperson":

        salesperson_id = (
            prefixed_id(
                value
            )
        )

        if salesperson_id:

            return (
                "CAST(sp.salesperson_id AS TEXT) = :scope_id",
                {
                    "scope_id":
                        salesperson_id,
                },
            )

        return (
            "sp.salesperson_name = :scope_value",
            {
                "scope_value":
                    value,
            },
        )


    raise ValueError(
        f"Unsupported scope dimension: {dimension}"
    )


# ============================================================
# BREAKDOWN EXPRESSIONS
# ============================================================

BREAKDOWN_EXPRESSIONS = {

    "region":
        "s.region",

    "city":
        "s.city",

    "channel":
        "s.channel",

    "category":
        "p.category",

    "brand":
        "p.brand",

    "product":
        (
            "CONCAT("
            "CAST(p.product_id AS TEXT), "
            "' | ', "
            "p.product_name"
            ")"
        ),

    "store":
        (
            "CONCAT("
            "CAST(s.store_id AS TEXT), "
            "' | ', "
            "s.store_name"
            ")"
        ),

    "salesperson":
        (
            "CONCAT("
            "CAST(sp.salesperson_id AS TEXT), "
            "' | ', "
            "sp.salesperson_name"
            ")"
        ),
}


# ============================================================
# DEFAULT DRILLDOWNS
# ============================================================

def default_breakdowns(
    dimension: str,
) -> list[str]:

    mapping = {

        "overall": [
            "region",
            "category",
            "product",
        ],

        "region": [
            "product",
            "channel",
            "store",
        ],

        "city": [
            "product",
            "channel",
            "store",
        ],

        "channel": [
            "product",
            "region",
            "store",
        ],

        "category": [
            "product",
            "region",
            "channel",
        ],

        "brand": [
            "product",
            "region",
            "channel",
        ],

        "product": [
            "region",
            "channel",
            "store",
        ],

        "store": [
            "product",
            "category",
        ],

        "salesperson": [
            "product",
            "region",
            "channel",
        ],
    }

    return mapping.get(
        dimension,
        [
            "region",
            "product",
        ],
    )