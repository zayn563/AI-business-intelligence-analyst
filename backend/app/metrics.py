# ============================================================
# SALES METRIC REGISTRY
#
# The LLM will NEVER define these calculations.
#
# Every supported business metric has one controlled
# SQL definition here.
# ============================================================


SALES_METRICS = {

    "net_sales": {
        "label": "Net Sales",
        "expression": "SUM(f.net_sales)",
        "format": "currency",
    },

    "gross_sales": {
        "label": "Gross Sales",
        "expression": "SUM(f.gross_sales)",
        "format": "currency",
    },

    "units_sold": {
        "label": "Units Sold",
        "expression": "SUM(f.units_sold)",
        "format": "integer",
    },

    "transactions": {
        "label": "Transactions",
        "expression": "SUM(f.transactions)",
        "format": "integer",
    },

    "gross_profit": {
        "label": "Gross Profit",
        "expression": """
            SUM(
                f.net_sales
                - f.cogs
            )
        """,
        "format": "currency",
    },

    "margin_pct": {
        "label": "Gross Margin %",
        "expression": """
            100.0
            * SUM(
                f.net_sales - f.cogs
            )
            / NULLIF(
                SUM(f.net_sales),
                0
            )
        """,
        "format": "percentage",
    },

    "avg_selling_price": {
        "label": "Average Selling Price",
        "expression": """
            SUM(f.net_sales)
            / NULLIF(
                SUM(f.units_sold),
                0
            )
        """,
        "format": "currency",
    },

    "discount_pct": {
        "label": "Discount %",
        "expression": """
            100.0
            * SUM(f.discount_amount)
            / NULLIF(
                SUM(f.gross_sales),
                0
            )
        """,
        "format": "percentage",
    },

    "returns_value": {
        "label": "Returns Value",
        "expression": "SUM(f.returns_value)",
        "format": "currency",
    },
}


# ============================================================
# DIMENSIONS
# ============================================================

SALES_DIMENSIONS = {

    "region":
        "s.region",

    "city":
        "s.city",

    "channel":
        "s.channel",

    "store":
        "s.store_name",

    "product":
        "p.product_name",

    "brand":
        "p.brand",

    "category":
        "p.category",

    "subcategory":
        "p.subcategory",

    "salesperson":
        "sp.salesperson_name",

    "date":
        "f.date_id",

    "month":
        "DATE_TRUNC('month', f.date_id)::date",

    "quarter":
        """
        DATE_TRUNC(
            'quarter',
            f.date_id
        )::date
        """,

    "year":
        "EXTRACT(YEAR FROM f.date_id)::integer",
}


# ============================================================
# FILTERS
# ============================================================

SALES_FILTERS = {

    "region":
        "s.region",

    "city":
        "s.city",

    "channel":
        "s.channel",

    "store":
        "s.store_name",

    "product":
        "p.product_name",

    "brand":
        "p.brand",

    "category":
        "p.category",

    "subcategory":
        "p.subcategory",

    "salesperson":
        "sp.salesperson_name",
}


SUPPORTED_METRICS = set(
    SALES_METRICS.keys()
)

SUPPORTED_DIMENSIONS = set(
    SALES_DIMENSIONS.keys()
)

SUPPORTED_FILTERS = set(
    SALES_FILTERS.keys()
)