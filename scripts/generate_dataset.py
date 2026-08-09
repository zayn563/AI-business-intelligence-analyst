from pathlib import Path
import json

import numpy as np
import pandas as pd
from faker import Faker


# ============================================================
# PROJECT CONFIGURATION
# ============================================================

SEED = 42

START_DATE = "2025-01-01"
END_DATE = "2026-07-31"

NUM_STORES = 60
NUM_PRODUCTS = 20
NUM_SALESPERSONS = 10

# 60 stores × 20 products × 577 days × 65%
# gives us approximately 450,000 sales observations.
ACTIVE_COMBINATION_RATE = 0.65


# ============================================================
# PATHS
# ============================================================

ROOT = Path(__file__).resolve().parents[1]

OUTPUT_DIR = ROOT / "data" / "generated"

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# RANDOM SEEDS
#
# Using fixed seeds makes the dataset reproducible.
# ============================================================

rng = np.random.default_rng(SEED)

fake = Faker()

Faker.seed(SEED)


# ============================================================
# BUSINESS MASTER DATA
# ============================================================

REGIONS = {
    "North": [
        "Northville",
        "Hillford",
    ],
    "South": [
        "Southport",
        "Baytown",
    ],
    "East": [
        "Easton",
        "Lakeview",
    ],
    "West": [
        "Westfield",
        "Riverton",
    ],
    "Central": [
        "Centerville",
        "Midtown",
    ],
}


# Channel factor represents relative store demand.
CHANNEL_FACTORS = {
    "Grocery": 0.80,
    "Convenience": 1.10,
    "Supermarket": 1.50,
    "Hypermarket": 2.00,
    "Pharmacy": 0.70,
    "Wholesale": 1.30,
}


CHANNEL_PROBABILITIES = {
    "Grocery": 0.30,
    "Convenience": 0.25,
    "Supermarket": 0.18,
    "Hypermarket": 0.07,
    "Pharmacy": 0.10,
    "Wholesale": 0.10,
}


# ------------------------------------------------------------
# Product fields:
#
# product_name
# brand
# category
# subcategory
# pack_size
# list_price
# standard_cost
# ------------------------------------------------------------

PRODUCT_CATALOG = [

    (
        "Energy Drink 250ml",
        "Volt",
        "Beverages",
        "Energy Drinks",
        "250ml",
        2.50,
        1.35,
    ),

    (
        "Energy Drink 355ml",
        "Volt",
        "Beverages",
        "Energy Drinks",
        "355ml",
        3.20,
        1.70,
    ),

    (
        "Cola 330ml",
        "Fizz",
        "Beverages",
        "Carbonated Drinks",
        "330ml",
        1.40,
        0.70,
    ),

    (
        "Orange Juice 250ml",
        "FreshGo",
        "Beverages",
        "Juice",
        "250ml",
        2.20,
        1.20,
    ),

    (
        "Mineral Water 500ml",
        "Pure",
        "Beverages",
        "Water",
        "500ml",
        1.00,
        0.40,
    ),

    (
        "Potato Chips",
        "Crunch",
        "Snacks",
        "Chips",
        "50g",
        1.70,
        0.85,
    ),

    (
        "Chocolate Bar",
        "Cocoa",
        "Snacks",
        "Chocolate",
        "45g",
        1.80,
        0.95,
    ),

    (
        "Biscuits",
        "DailyBite",
        "Snacks",
        "Biscuits",
        "100g",
        1.50,
        0.75,
    ),

    (
        "Protein Bar",
        "Active",
        "Snacks",
        "Health Snacks",
        "60g",
        2.80,
        1.55,
    ),

    (
        "Mixed Nuts",
        "Nature",
        "Snacks",
        "Nuts",
        "100g",
        3.50,
        2.00,
    ),

    (
        "Shampoo 250ml",
        "CarePlus",
        "Personal Care",
        "Hair Care",
        "250ml",
        5.50,
        3.20,
    ),

    (
        "Soap Bar",
        "Clean",
        "Personal Care",
        "Body Care",
        "100g",
        1.20,
        0.60,
    ),

    (
        "Toothpaste",
        "Bright",
        "Personal Care",
        "Oral Care",
        "120g",
        3.20,
        1.80,
    ),

    (
        "Face Wash",
        "Glow",
        "Personal Care",
        "Skin Care",
        "100ml",
        4.50,
        2.60,
    ),

    (
        "Deodorant",
        "Fresh",
        "Personal Care",
        "Deodorant",
        "150ml",
        4.00,
        2.10,
    ),

    (
        "Laundry Detergent",
        "HomePro",
        "Household",
        "Laundry",
        "1kg",
        6.50,
        4.00,
    ),

    (
        "Dishwashing Liquid",
        "Spark",
        "Household",
        "Kitchen Cleaning",
        "500ml",
        3.20,
        1.80,
    ),

    (
        "Tissue Box",
        "Soft",
        "Household",
        "Paper Products",
        "Standard",
        2.20,
        1.20,
    ),

    (
        "Surface Cleaner",
        "HomePro",
        "Household",
        "Cleaning",
        "500ml",
        4.20,
        2.40,
    ),

    (
        "Trash Bags",
        "StrongBag",
        "Household",
        "Utility",
        "20 Pack",
        3.00,
        1.60,
    ),
]


# ============================================================
# DATE DIMENSION
# ============================================================

print("\n[1/8] Generating date dimension...")


dates = pd.date_range(
    START_DATE,
    END_DATE,
    freq="D",
)


dim_date = pd.DataFrame(
    {
        "date_id": dates,
        "year": dates.year,
        "quarter": dates.quarter,
        "month": dates.month,
        "month_name": dates.month_name(),
        "week": dates.isocalendar().week.astype(int),
        "day_of_month": dates.day,
        "day_of_week": dates.dayofweek + 1,
        "day_name": dates.day_name(),
        "is_weekend": dates.dayofweek >= 5,
    }
)


dim_date.to_csv(
    OUTPUT_DIR / "dim_date.csv",
    index=False,
)


# ============================================================
# STORE DIMENSION
# ============================================================

print("[2/8] Generating stores...")


region_names = list(REGIONS.keys())

channel_names = list(CHANNEL_FACTORS.keys())

channel_probabilities = [
    CHANNEL_PROBABILITIES[channel]
    for channel in channel_names
]


store_rows = []


# Fixed range keeps generation reproducible.
opening_dates = pd.date_range(
    "2014-01-01",
    "2024-12-31",
    freq="D",
)


for store_id in range(
    1,
    NUM_STORES + 1,
):

    # Gives approximately equal store representation
    # across the five regions.
    region = region_names[
        (store_id - 1) % len(region_names)
    ]

    city = rng.choice(
        REGIONS[region]
    )

    channel = rng.choice(
        channel_names,
        p=channel_probabilities,
    )

    opened_date = rng.choice(
        opening_dates
    )

    store_rows.append(
        {
            "store_id": store_id,

            "store_name":
                f"{channel} Store {store_id:03d}",

            "city":
                city,

            "region":
                region,

            "channel":
                channel,

            "store_format":
                channel,

            "latitude":
                round(
                    rng.uniform(
                        24.0,
                        33.0,
                    ),
                    7,
                ),

            "longitude":
                round(
                    rng.uniform(
                        67.0,
                        74.0,
                    ),
                    7,
                ),

            "opened_date":
                pd.Timestamp(
                    opened_date
                ).date(),
        }
    )


dim_store = pd.DataFrame(
    store_rows
)


dim_store.to_csv(
    OUTPUT_DIR / "dim_store.csv",
    index=False,
)


# ============================================================
# PRODUCT DIMENSION
# ============================================================

print("[3/8] Generating products...")


product_rows = []


for product_id, product in enumerate(
    PRODUCT_CATALOG,
    start=1,
):

    (
        product_name,
        brand,
        category,
        subcategory,
        pack_size,
        list_price,
        standard_cost,
    ) = product


    product_rows.append(
        {
            "product_id":
                product_id,

            "product_name":
                product_name,

            "brand":
                brand,

            "category":
                category,

            "subcategory":
                subcategory,

            "pack_size":
                pack_size,

            "list_price":
                list_price,

            "standard_cost":
                standard_cost,
        }
    )


dim_product = pd.DataFrame(
    product_rows
)


dim_product.to_csv(
    OUTPUT_DIR / "dim_product.csv",
    index=False,
)


# ============================================================
# SALESPERSON DIMENSION
# ============================================================

print("[4/8] Generating salespeople...")


salesperson_rows = []


for salesperson_id in range(
    1,
    NUM_SALESPERSONS + 1,
):

    region = region_names[
        (salesperson_id - 1)
        % len(region_names)
    ]

    salesperson_rows.append(
        {
            "salesperson_id":
                salesperson_id,

            "salesperson_name":
                fake.name(),

            "region":
                region,

            "team":
                f"{region} Commercial Team",

            "manager_name":
                f"{region} Sales Manager",
        }
    )


dim_salesperson = pd.DataFrame(
    salesperson_rows
)


dim_salesperson.to_csv(
    OUTPUT_DIR / "dim_salesperson.csv",
    index=False,
)


# ============================================================
# LOOKUP MAPS
# ============================================================

store_map = (
    dim_store
    .set_index("store_id")
    .to_dict("index")
)


product_map = (
    dim_product
    .set_index("product_id")
    .to_dict("index")
)


# ============================================================
# SALES + INVENTORY FACT TABLES
# ============================================================

print(
    "[5/8] Generating sales and inventory..."
)

print(
    "      This is the largest step."
)


sales_rows = []

inventory_rows = []


for store_id in range(
    1,
    NUM_STORES + 1,
):

    store = store_map[
        store_id
    ]

    region = store[
        "region"
    ]

    channel_factor = (
        CHANNEL_FACTORS[
            store["channel"]
        ]
    )


    # Find salespeople assigned to this region.
    region_salespeople = (
        dim_salesperson[
            dim_salesperson[
                "region"
            ] == region
        ]
    )


    salesperson_id = int(
        rng.choice(
            region_salespeople[
                "salesperson_id"
            ]
        )
    )


    for product_id in range(
        1,
        NUM_PRODUCTS + 1,
    ):

        product = product_map[
            product_id
        ]


        # Creates different demand levels by store/product.
        base_units = rng.uniform(
            8,
            35,
        )


        for date in dates:

            # Not every product is active in every shop
            # every day.
            if (
                rng.random()
                > ACTIVE_COMBINATION_RATE
            ):
                continue


            # ------------------------------------------------
            # NORMAL BUSINESS DEMAND
            # ------------------------------------------------

            weekend_factor = (
                1.15
                if date.dayofweek >= 5
                else 1.00
            )


            seasonal_factor = (
                1
                + 0.10
                * np.sin(
                    2
                    * np.pi
                    * date.dayofyear
                    / 365
                )
            )


            demand = (
                base_units
                * channel_factor
                * weekend_factor
                * seasonal_factor
            )


            # Normal random demand noise.
            demand *= rng.normal(
                1.0,
                0.12,
            )


            # =================================================
            # HIDDEN BUSINESS SCENARIO 1
            #
            # NORTH REGION DECLINE
            #
            # June 2026
            #
            # Demand falls 18%.
            # Stockout probability also increases.
            # =================================================

            north_decline = (
                region == "North"

                and

                pd.Timestamp(
                    "2026-06-01"
                )
                <= date
                <=
                pd.Timestamp(
                    "2026-06-30"
                )
            )


            if north_decline:
                demand *= 0.82


            # =================================================
            # HIDDEN BUSINESS SCENARIO 2
            #
            # PRODUCT 5 PROMOTION
            #
            # April 2026
            #
            # Demand increases 35%.
            # Discount becomes 18%.
            # =================================================

            promo_active = (
                product_id == 5

                and

                pd.Timestamp(
                    "2026-04-01"
                )
                <= date
                <=
                pd.Timestamp(
                    "2026-04-30"
                )
            )


            if promo_active:
                demand *= 1.35


            demand_units = max(
                int(
                    round(demand)
                ),
                0,
            )


            # =================================================
            # INVENTORY
            # =================================================

            normal_stockout_probability = (
                0.025
            )


            if north_decline:

                stockout_probability = (
                    0.14
                )

            else:

                stockout_probability = (
                    normal_stockout_probability
                )


            intentional_stockout = (
                rng.random()
                < stockout_probability
            )


            if intentional_stockout:

                # Shop cannot satisfy full demand.
                available_stock = max(
                    int(
                        demand_units
                        * rng.uniform(
                            0.25,
                            0.70,
                        )
                    ),
                    0,
                )

            else:

                # Enough inventory to satisfy demand.
                available_stock = max(
                    int(
                        demand_units
                        * rng.uniform(
                            1.20,
                            2.50,
                        )
                    ),
                    demand_units,
                )


            units_sold = min(
                demand_units,
                available_stock,
            )


            opening_stock = max(
                int(
                    available_stock
                    * rng.uniform(
                        0.40,
                        0.90,
                    )
                ),
                0,
            )


            received_units = max(
                available_stock
                - opening_stock,
                0,
            )


            closing_stock = max(
                available_stock
                - units_sold,
                0,
            )


            # We use our deliberately generated stockout
            # event rather than simply closing_stock == 0.
            stockout_flag = (
                intentional_stockout
            )


            # =================================================
            # PRICE
            # =================================================

            unit_price = float(
                product[
                    "list_price"
                ]
            )


            # =================================================
            # HIDDEN BUSINESS SCENARIO 3
            #
            # PRODUCT 10 PRICE-LED GROWTH
            #
            # July 2026
            #
            # Selling price increases by 11%.
            # =================================================

            price_growth = (
                product_id == 10

                and

                pd.Timestamp(
                    "2026-07-01"
                )
                <= date
                <=
                pd.Timestamp(
                    "2026-07-31"
                )
            )


            if price_growth:
                unit_price *= 1.11


            # -------------------------------------------------
            # STANDARD DISCOUNTS
            # -------------------------------------------------

            discount_pct = rng.uniform(
                0.00,
                0.05,
            )


            if promo_active:

                discount_pct = 0.18


            # =================================================
            # HIDDEN BUSINESS SCENARIO 4
            #
            # SOUTH REGION MARGIN DETERIORATION
            #
            # July 2026
            #
            # Extra discount + higher product costs.
            # =================================================

            south_margin_issue = (
                region == "South"

                and

                pd.Timestamp(
                    "2026-07-01"
                )
                <= date
                <=
                pd.Timestamp(
                    "2026-07-31"
                )
            )


            if south_margin_issue:

                discount_pct += 0.08


            # =================================================
            # SALES CALCULATIONS
            # =================================================

            gross_sales = (
                units_sold
                * unit_price
            )


            discount_amount = (
                gross_sales
                * discount_pct
            )


            net_sales_before_returns = (
                gross_sales
                - discount_amount
            )


            unit_cost = float(
                product[
                    "standard_cost"
                ]
            )


            if south_margin_issue:

                unit_cost *= 1.10


            cogs = (
                units_sold
                * unit_cost
            )


            # -------------------------------------------------
            # Returns
            #
            # About 1.5% of observations may contain returns.
            # -------------------------------------------------

            if rng.random() < 0.015:

                return_rate = rng.uniform(
                    0.01,
                    0.04,
                )

            else:

                return_rate = 0.0


            returns_value = (
                net_sales_before_returns
                * return_rate
            )


            net_sales = (
                net_sales_before_returns
                - returns_value
            )


            # -------------------------------------------------
            # Transactions
            # -------------------------------------------------

            if units_sold > 0:

                transactions = max(
                    int(
                        units_sold
                        /
                        rng.uniform(
                            1.10,
                            2.50,
                        )
                    ),
                    1,
                )

            else:

                transactions = 0


            # =================================================
            # SALES FACT ROW
            # =================================================

            sales_rows.append(
                {
                    "date_id":
                        date.date(),

                    "store_id":
                        store_id,

                    "product_id":
                        product_id,

                    "salesperson_id":
                        salesperson_id,

                    "units_sold":
                        units_sold,

                    "transactions":
                        transactions,

                    "gross_sales":
                        round(
                            gross_sales,
                            2,
                        ),

                    "discount_amount":
                        round(
                            discount_amount,
                            2,
                        ),

                    "net_sales":
                        round(
                            net_sales,
                            2,
                        ),

                    "cogs":
                        round(
                            cogs,
                            2,
                        ),

                    "returns_value":
                        round(
                            returns_value,
                            2,
                        ),

                    "promo_flag":
                        promo_active,
                }
            )


            # =================================================
            # INVENTORY FACT ROW
            # =================================================

            inventory_rows.append(
                {
                    "date_id":
                        date.date(),

                    "store_id":
                        store_id,

                    "product_id":
                        product_id,

                    "opening_stock":
                        opening_stock,

                    "received_units":
                        received_units,

                    "closing_stock":
                        closing_stock,

                    "stockout_flag":
                        stockout_flag,
                }
            )


# ============================================================
# CREATE DATAFRAMES
# ============================================================

fact_sales = pd.DataFrame(
    sales_rows
)


fact_inventory = pd.DataFrame(
    inventory_rows
)


fact_sales.to_csv(
    OUTPUT_DIR / "fact_sales_daily.csv",
    index=False,
)


fact_inventory.to_csv(
    OUTPUT_DIR / "fact_inventory_daily.csv",
    index=False,
)


# ============================================================
# MONTHLY TARGETS
# ============================================================

print(
    "[6/8] Generating monthly targets..."
)


sales_for_targets = (
    fact_sales

    .merge(
        dim_store[
            [
                "store_id",
                "region",
            ]
        ],
        on="store_id",
    )

    .merge(
        dim_product[
            [
                "product_id",
                "category",
            ]
        ],
        on="product_id",
    )
)


sales_for_targets[
    "month_start"
] = (
    pd.to_datetime(
        sales_for_targets[
            "date_id"
        ]
    )
    .dt.to_period("M")
    .dt.to_timestamp()
)


monthly_actuals = (
    sales_for_targets

    .groupby(
        [
            "month_start",
            "region",
            "category",
        ],
        as_index=False,
    )

    .agg(
        actual_sales=(
            "net_sales",
            "sum",
        ),

        actual_units=(
            "units_sold",
            "sum",
        ),

        actual_cogs=(
            "cogs",
            "sum",
        ),
    )
)


target_rows = []


for _, row in monthly_actuals.iterrows():

    # Normal targets sit slightly around actual performance.
    target_multiplier = rng.uniform(
        0.98,
        1.08,
    )


    # ========================================================
    # HIDDEN BUSINESS SCENARIO 5
    #
    # EAST REGION TARGET MISS
    #
    # July 2026
    #
    # Actual / target = approximately 86%.
    # ========================================================

    if (
        row["region"] == "East"

        and

        row["month_start"]
        == pd.Timestamp(
            "2026-07-01"
        )
    ):

        target_multiplier = (
            1 / 0.86
        )


    target_rows.append(
        {
            "month_start":
                row[
                    "month_start"
                ].date(),

            "region":
                row[
                    "region"
                ],

            "category":
                row[
                    "category"
                ],

            "sales_target":
                round(
                    row[
                        "actual_sales"
                    ]
                    * target_multiplier,
                    2,
                ),

            "units_target":
                int(
                    round(
                        row[
                            "actual_units"
                        ]
                        * target_multiplier
                    )
                ),

            "margin_target_pct":
                round(
                    rng.uniform(
                        0.25,
                        0.38,
                    ),
                    4,
                ),
        }
    )


fact_targets = pd.DataFrame(
    target_rows
)


fact_targets.to_csv(
    OUTPUT_DIR
    / "fact_targets_monthly.csv",
    index=False,
)


# ============================================================
# PROMOTION TABLE
# ============================================================

print(
    "[7/8] Generating promotions..."
)


fact_promotions = pd.DataFrame(
    [
        {
            "promotion_id":
                1,

            "product_id":
                5,

            # Blank region = national promotion.
            "region":
                "",

            "promotion_type":
                "Price Discount",

            "campaign_name":
                "April Product 5 Promotion",

            "start_date":
                "2026-04-01",

            "end_date":
                "2026-04-30",

            "discount_pct":
                0.18,
        }
    ]
)


fact_promotions.to_csv(
    OUTPUT_DIR
    / "fact_promotions.csv",
    index=False,
)


# ============================================================
# GROUND TRUTH
#
# IMPORTANT:
# This is our evaluation answer key.
#
# It will NOT be supplied to the future AI agent.
# ============================================================

print(
    "[8/8] Writing evaluation ground truth..."
)


ground_truth = {

    "scenario_1": {
        "name":
            "North Region Decline",

        "period":
            "June 2026",

        "expected_signal":
            (
                "North sales and units decline "
                "while stockout incidence increases."
            ),
    },


    "scenario_2": {
        "name":
            "Product 5 Promotion",

        "period":
            "April 2026",

        "expected_signal":
            (
                "Product 5 unit volume increases "
                "while discounting increases."
            ),
    },


    "scenario_3": {
        "name":
            "Product 10 Price-Led Growth",

        "period":
            "July 2026",

        "expected_signal":
            (
                "Product 10 selling price increases "
                "by approximately 11%, making revenue "
                "growth more price-driven than volume-driven."
            ),
    },


    "scenario_4": {
        "name":
            "South Margin Deterioration",

        "period":
            "July 2026",

        "expected_signal":
            (
                "South receives higher discounts "
                "and higher costs, reducing gross margin."
            ),
    },


    "scenario_5": {
        "name":
            "East Target Miss",

        "period":
            "July 2026",

        "expected_signal":
            (
                "East target achievement should be "
                "approximately 86%."
            ),
    },
}


with open(
    OUTPUT_DIR / "ground_truth.json",
    "w",
    encoding="utf-8",
) as file:

    json.dump(
        ground_truth,
        file,
        indent=4,
    )


# ============================================================
# DATASET SUMMARY
# ============================================================

print(
    "\n============================================"
)

print(
    "DATASET GENERATION COMPLETE"
)

print(
    "============================================"
)


print(
    f"Date records:       {len(dim_date):,}"
)

print(
    f"Stores:             {len(dim_store):,}"
)

print(
    f"Products:           {len(dim_product):,}"
)

print(
    f"Salespeople:        {len(dim_salesperson):,}"
)

print(
    f"Sales records:      {len(fact_sales):,}"
)

print(
    f"Inventory records:  {len(fact_inventory):,}"
)

print(
    f"Target records:     {len(fact_targets):,}"
)

print(
    f"Promotions:         {len(fact_promotions):,}"
)


print(
    "\nDate range:"
)

print(
    f"{START_DATE} to {END_DATE}"
)


print(
    "\nGenerated files:"
)


for file_path in sorted(
    OUTPUT_DIR.iterdir()
):

    print(
        f" - {file_path.name}"
    )


print(
    "\nOutput directory:"
)

print(
    OUTPUT_DIR
)