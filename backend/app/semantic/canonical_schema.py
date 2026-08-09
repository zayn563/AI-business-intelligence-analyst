# ============================================================
# CANONICAL SALES SCHEMA
#
# This file defines the business meaning expected by the
# analytics platform.
#
# Incoming datasets may use different column names, but the
# semantic mapping layer converts them into these canonical
# fields.
# ============================================================


CANONICAL_FIELDS = {

    # ========================================================
    # TIME
    # ========================================================

    "date": {
        "label": "Transaction Date",
        "expected_type": "date",
        "role": "date",
        "importance": "core",
        "warehouse_target":
            "analytics.fact_sales_daily.date_id",
    },


    # ========================================================
    # IDENTIFIERS
    # ========================================================

    "store_id": {
        "label": "Store ID",
        "expected_type": "identifier",
        "role": "identifier",
        "importance": "recommended",
        "warehouse_target":
            "analytics.fact_sales_daily.store_id",
    },

    "product_id": {
        "label": "Product ID",
        "expected_type": "identifier",
        "role": "identifier",
        "importance": "recommended",
        "warehouse_target":
            "analytics.fact_sales_daily.product_id",
    },

    "salesperson_id": {
        "label": "Salesperson ID",
        "expected_type": "identifier",
        "role": "identifier",
        "importance": "optional",
        "warehouse_target":
            "analytics.fact_sales_daily.salesperson_id",
    },


    # ========================================================
    # BUSINESS DIMENSIONS
    # ========================================================

    "region": {
        "label": "Region",
        "expected_type": "categorical",
        "role": "dimension",
        "importance": "recommended",
        "warehouse_target":
            "analytics.dim_store.region",
    },

    "city": {
        "label": "City",
        "expected_type": "categorical",
        "role": "dimension",
        "importance": "optional",
        "warehouse_target":
            "analytics.dim_store.city",
    },

    "channel": {
        "label": "Channel",
        "expected_type": "categorical",
        "role": "dimension",
        "importance": "optional",
        "warehouse_target":
            "analytics.dim_store.channel",
    },

    "store": {
        "label": "Store",
        "expected_type": "categorical",
        "role": "dimension",
        "importance": "recommended",
        "warehouse_target":
            "analytics.dim_store.store_name",
    },

    "product": {
        "label": "Product",
        "expected_type": "categorical",
        "role": "dimension",
        "importance": "recommended",
        "warehouse_target":
            "analytics.dim_product.product_name",
    },

    "brand": {
        "label": "Brand",
        "expected_type": "categorical",
        "role": "dimension",
        "importance": "optional",
        "warehouse_target":
            "analytics.dim_product.brand",
    },

    "category": {
        "label": "Category",
        "expected_type": "categorical",
        "role": "dimension",
        "importance": "recommended",
        "warehouse_target":
            "analytics.dim_product.category",
    },

    "subcategory": {
        "label": "Subcategory",
        "expected_type": "categorical",
        "role": "dimension",
        "importance": "optional",
        "warehouse_target":
            "analytics.dim_product.subcategory",
    },

    "salesperson": {
        "label": "Salesperson",
        "expected_type": "categorical",
        "role": "dimension",
        "importance": "optional",
        "warehouse_target":
            "analytics.dim_salesperson.salesperson_name",
    },


    # ========================================================
    # CORE SALES MEASURES
    # ========================================================

    "net_sales": {
        "label": "Net Sales",
        "expected_type": "numeric",
        "role": "measure",
        "importance": "core",
        "warehouse_target":
            "analytics.fact_sales_daily.net_sales",
    },

    "gross_sales": {
        "label": "Gross Sales",
        "expected_type": "numeric",
        "role": "measure",
        "importance": "optional",
        "warehouse_target":
            "analytics.fact_sales_daily.gross_sales",
    },

    "units_sold": {
        "label": "Units Sold",
        "expected_type": "numeric",
        "role": "measure",
        "importance": "recommended",
        "warehouse_target":
            "analytics.fact_sales_daily.units_sold",
    },

    "transactions": {
        "label": "Transactions",
        "expected_type": "numeric",
        "role": "measure",
        "importance": "optional",
        "warehouse_target":
            "analytics.fact_sales_daily.transactions",
    },

    "discount_amount": {
        "label": "Discount Amount",
        "expected_type": "numeric",
        "role": "measure",
        "importance": "optional",
        "warehouse_target":
            "analytics.fact_sales_daily.discount_amount",
    },

    "cogs": {
        "label": "Cost of Goods Sold",
        "expected_type": "numeric",
        "role": "measure",
        "importance": "recommended",
        "warehouse_target":
            "analytics.fact_sales_daily.cogs",
    },

    "returns_value": {
        "label": "Returns Value",
        "expected_type": "numeric",
        "role": "measure",
        "importance": "optional",
        "warehouse_target":
            "analytics.fact_sales_daily.returns_value",
    },

    "promo_flag": {
        "label": "Promotion Flag",
        "expected_type": "boolean",
        "role": "flag",
        "importance": "optional",
        "warehouse_target":
            "analytics.fact_sales_daily.promo_flag",
    },


    # ========================================================
    # INVENTORY
    # ========================================================

    "opening_stock": {
        "label": "Opening Stock",
        "expected_type": "numeric",
        "role": "measure",
        "importance": "optional",
        "warehouse_target":
            "analytics.fact_inventory_daily.opening_stock",
    },

    "received_units": {
        "label": "Received Units",
        "expected_type": "numeric",
        "role": "measure",
        "importance": "optional",
        "warehouse_target":
            "analytics.fact_inventory_daily.received_units",
    },

    "closing_stock": {
        "label": "Closing Stock",
        "expected_type": "numeric",
        "role": "measure",
        "importance": "optional",
        "warehouse_target":
            "analytics.fact_inventory_daily.closing_stock",
    },

    "stockout_flag": {
        "label": "Stockout Flag",
        "expected_type": "boolean",
        "role": "flag",
        "importance": "optional",
        "warehouse_target":
            "analytics.fact_inventory_daily.stockout_flag",
    },


    # ========================================================
    # TARGETS
    # ========================================================

    "sales_target": {
        "label": "Sales Target",
        "expected_type": "numeric",
        "role": "measure",
        "importance": "optional",
        "warehouse_target":
            "analytics.fact_targets_monthly.sales_target",
    },

    "units_target": {
        "label": "Units Target",
        "expected_type": "numeric",
        "role": "measure",
        "importance": "optional",
        "warehouse_target":
            "analytics.fact_targets_monthly.units_target",
    },

    "margin_target_pct": {
        "label": "Margin Target %",
        "expected_type": "numeric",
        "role": "measure",
        "importance": "optional",
        "warehouse_target":
            "analytics.fact_targets_monthly.margin_target_pct",
    },
}


# ============================================================
# DIMENSION FIELDS
# ============================================================

DIMENSION_FIELDS = [
    "region",
    "city",
    "channel",
    "store",
    "product",
    "brand",
    "category",
    "subcategory",
    "salesperson",
]


# ============================================================
# METRIC DEPENDENCIES
#
# A metric is available only when all required source fields
# have successfully been mapped.
# ============================================================

METRIC_DEFINITIONS = {

    "net_sales": {
        "label": "Net Sales",
        "kind": "direct",
        "requires": [
            "net_sales",
        ],
    },

    "gross_sales": {
        "label": "Gross Sales",
        "kind": "direct",
        "requires": [
            "gross_sales",
        ],
    },

    "units_sold": {
        "label": "Units Sold",
        "kind": "direct",
        "requires": [
            "units_sold",
        ],
    },

    "transactions": {
        "label": "Transactions",
        "kind": "direct",
        "requires": [
            "transactions",
        ],
    },

    "returns_value": {
        "label": "Returns Value",
        "kind": "direct",
        "requires": [
            "returns_value",
        ],
    },

    "gross_profit": {
        "label": "Gross Profit",
        "kind": "derived",
        "requires": [
            "net_sales",
            "cogs",
        ],
    },

    "margin_pct": {
        "label": "Gross Margin %",
        "kind": "derived",
        "requires": [
            "net_sales",
            "cogs",
        ],
    },

    "avg_selling_price": {
        "label": "Average Selling Price",
        "kind": "derived",
        "requires": [
            "net_sales",
            "units_sold",
        ],
    },

    "discount_pct": {
        "label": "Discount %",
        "kind": "derived",
        "requires": [
            "gross_sales",
            "discount_amount",
        ],
    },

    "stockout_rate": {
        "label": "Stockout Rate",
        "kind": "derived",
        "requires": [
            "stockout_flag",
        ],
    },

    "target_achievement_pct": {
        "label": "Sales Target Achievement %",
        "kind": "derived",
        "requires": [
            "net_sales",
            "sales_target",
        ],
    },
}


# ============================================================
# ANALYSIS CAPABILITY REQUIREMENTS
# ============================================================

ANALYSIS_REQUIREMENTS = {

    "summary": {
        "all_of": [
            "net_sales",
        ],
    },

    "trend": {
        "all_of": [
            "date",
            "net_sales",
        ],
    },

    "comparison": {
        "all_of": [
            "date",
            "net_sales",
        ],
    },

    "ranking": {
        "all_of": [
            "net_sales",
        ],
        "any_of": DIMENSION_FIELDS,
    },

    "breakdown": {
        "all_of": [
            "net_sales",
        ],
        "any_of": DIMENSION_FIELDS,
    },

    "price_volume_analysis": {
        "all_of": [
            "net_sales",
            "units_sold",
        ],
    },

    "margin_analysis": {
        "all_of": [
            "net_sales",
            "cogs",
        ],
    },

    "discount_analysis": {
        "all_of": [
            "gross_sales",
            "discount_amount",
        ],
    },

    "inventory_analysis": {
        "all_of": [
            "stockout_flag",
        ],
    },

    "target_analysis": {
        "all_of": [
            "net_sales",
            "sales_target",
        ],
    },

    "promotion_analysis": {
        "all_of": [
            "promo_flag",
            "net_sales",
        ],
    },
}


# ============================================================
# CAPABILITY DETECTION
# ============================================================

def _requirements_met(
    definition: dict,
    available_fields: set[str],
) -> bool:

    all_of = set(
        definition.get(
            "all_of",
            []
        )
    )

    any_of = set(
        definition.get(
            "any_of",
            []
        )
    )


    if not all_of.issubset(
        available_fields
    ):
        return False


    if any_of:

        if not (
            any_of
            & available_fields
        ):
            return False


    return True


def evaluate_capabilities(
    available_fields: set[str],
) -> dict:

    # --------------------------------------------------------
    # Available metrics
    # --------------------------------------------------------

    available_metrics = []

    unavailable_metrics = {}


    for (
        metric_name,
        definition,
    ) in METRIC_DEFINITIONS.items():

        required = set(
            definition[
                "requires"
            ]
        )


        missing = (
            required
            - available_fields
        )


        if not missing:

            available_metrics.append(
                metric_name
            )

        else:

            unavailable_metrics[
                metric_name
            ] = sorted(
                missing
            )


    # --------------------------------------------------------
    # Dimensions
    # --------------------------------------------------------

    available_dimensions = [

        field

        for field in DIMENSION_FIELDS

        if field
        in available_fields
    ]


    # --------------------------------------------------------
    # Analyses
    # --------------------------------------------------------

    available_analyses = []

    unavailable_analyses = {}


    for (
        analysis_name,
        definition,
    ) in ANALYSIS_REQUIREMENTS.items():

        if _requirements_met(
            definition,
            available_fields,
        ):

            available_analyses.append(
                analysis_name
            )

        else:

            missing_all = [

                field

                for field
                in definition.get(
                    "all_of",
                    []
                )

                if field
                not in available_fields
            ]


            any_of = (
                definition.get(
                    "any_of",
                    []
                )
            )


            missing_any_group = False


            if any_of:

                missing_any_group = not any(
                    field
                    in available_fields

                    for field
                    in any_of
                )


            unavailable_analyses[
                analysis_name
            ] = {

                "missing_required":
                    missing_all,

                "needs_one_of":
                    (
                        any_of
                        if missing_any_group
                        else []
                    ),
            }


    return {

        "available_fields":
            sorted(
                available_fields
            ),

        "available_metrics":
            sorted(
                available_metrics
            ),

        "unavailable_metrics":
            unavailable_metrics,

        "available_dimensions":
            sorted(
                available_dimensions
            ),

        "available_analyses":
            sorted(
                available_analyses
            ),

        "unavailable_analyses":
            unavailable_analyses,
    }


# ============================================================
# API PAYLOAD
# ============================================================

def canonical_schema_payload() -> dict:

    return {

        "canonical_fields":
            CANONICAL_FIELDS,

        "metric_definitions":
            METRIC_DEFINITIONS,

        "analysis_requirements":
            ANALYSIS_REQUIREMENTS,
    }