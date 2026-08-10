# ============================================================
# BUSINESS MATERIALITY RULES
#
# mode:
#   pct = percentage change
#   pp  = percentage-point change
#
# preferred:
#   higher  = increase generally positive
#   lower   = decrease generally positive
#   neutral = context dependent
# ============================================================

METRIC_RULES = {

    "net_sales": {
        "mode": "pct",
        "low": 5.0,
        "medium": 10.0,
        "high": 20.0,
        "preferred": "higher",
    },

    "units_sold": {
        "mode": "pct",
        "low": 5.0,
        "medium": 10.0,
        "high": 20.0,
        "preferred": "higher",
    },

    "transactions": {
        "mode": "pct",
        "low": 5.0,
        "medium": 10.0,
        "high": 20.0,
        "preferred": "higher",
    },

    "gross_profit": {
        "mode": "pct",
        "low": 5.0,
        "medium": 10.0,
        "high": 20.0,
        "preferred": "higher",
    },

    "margin_pct": {
        "mode": "pp",
        "low": 1.0,
        "medium": 2.0,
        "high": 4.0,
        "preferred": "higher",
    },

    "avg_selling_price": {
        "mode": "pct",
        "low": 2.0,
        "medium": 5.0,
        "high": 10.0,
        "preferred": "neutral",
    },

    "discount_pct": {
        "mode": "pp",
        "low": 2.0,
        "medium": 5.0,
        "high": 10.0,
        "preferred": "neutral",
    },

    "cost_per_unit": {
        "mode": "pct",
        "low": 3.0,
        "medium": 5.0,
        "high": 10.0,
        "preferred": "lower",
    },

    "stockout_rate": {
        "mode": "pp",
        "low": 2.0,
        "medium": 5.0,
        "high": 10.0,
        "preferred": "lower",
    },
}


SEVERITY_RANK = {
    "informational": 0,
    "low": 1,
    "medium": 2,
    "high": 3,
}