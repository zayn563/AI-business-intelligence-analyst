# ============================================================
# SALES FIELD ALIASES
#
# These aliases represent common alternative headers found
# in real sales, retail and FMCG datasets.
#
# Matching is case-insensitive and punctuation-insensitive
# after header normalization.
# ============================================================


FIELD_ALIASES = {

    # ========================================================
    # DATE
    # ========================================================

    "date": [
        "date",
        "sales date",
        "sale date",
        "transaction date",
        "transaction day",
        "invoice date",
        "billing date",
        "order date",
        "business date",
        "posting date",
        "record date",
        "day",
    ],


    # ========================================================
    # STORE IDENTIFICATION
    # ========================================================

    "store_id": [
        "store id",
        "store code",
        "shop id",
        "shop code",
        "outlet id",
        "outlet code",
        "customer id",
        "customer code",
        "retailer id",
        "retailer code",
        "account id",
        "account code",
    ],

    "store": [
        "store",
        "store name",
        "shop",
        "shop name",
        "outlet",
        "outlet name",
        "retailer",
        "retailer name",
        "customer",
        "customer name",
        "account name",
    ],

    "region": [
        "region",
        "region name",
        "sales region",
        "territory",
        "territory name",
        "sales territory",
        "zone",
        "zone name",
        "area",
        "area name",
        "market",
        "market region",
    ],

    "city": [
        "city",
        "city name",
        "town",
        "town name",
        "market city",
        "location city",
    ],

    "channel": [
        "channel",
        "channel name",
        "channel type",
        "sales channel",
        "trade channel",
        "retail channel",
        "outlet type",
        "store type",
    ],


    # ========================================================
    # PRODUCT IDENTIFICATION
    # ========================================================

    "product_id": [
        "product id",
        "product code",
        "sku",
        "sku id",
        "sku code",
        "item id",
        "item code",
        "material id",
        "material code",
    ],

    "product": [
        "product",
        "product name",
        "product description",
        "sku name",
        "sku description",
        "item",
        "item name",
        "item description",
        "material",
        "material name",
        "material description",
    ],

    "brand": [
        "brand",
        "brand name",
        "product brand",
    ],

    "category": [
        "category",
        "category name",
        "product category",
        "product group",
        "item category",
        "sales category",
        "cat",
    ],

    "subcategory": [
        "subcategory",
        "sub category",
        "sub-category",
        "subcategory name",
        "product subcategory",
        "product sub category",
    ],


    # ========================================================
    # SALESPERSON
    # ========================================================

    "salesperson_id": [
        "salesperson id",
        "sales person id",
        "sales rep id",
        "sales representative id",
        "rep id",
        "employee id",
    ],

    "salesperson": [
        "salesperson",
        "sales person",
        "salesperson name",
        "sales person name",
        "sales rep",
        "sales rep name",
        "sales representative",
        "sales representative name",
        "rep name",
    ],


    # ========================================================
    # SALES VALUES
    # ========================================================

    "net_sales": [
        "net sales",
        "sales",
        "sales amount",
        "sales value",
        "net sales value",
        "net sales amount",
        "net revenue",
        "revenue",
        "revenue amount",
        "total sales",
        "total revenue",
        "sales revenue",
        "nsv",
    ],

    "gross_sales": [
        "gross sales",
        "gross sales value",
        "gross sales amount",
        "gross revenue",
        "gross value",
        "sales before discount",
        "revenue before discount",
        "gsv",
    ],

    "units_sold": [
        "units sold",
        "units",
        "quantity",
        "qty",
        "sales qty",
        "sales quantity",
        "sold quantity",
        "sold qty",
        "volume",
        "sales volume",
        "unit sales",
    ],

    "transactions": [
        "transactions",
        "transaction count",
        "number of transactions",
        "invoice count",
        "receipt count",
        "bills",
        "bill count",
    ],

    "discount_amount": [
        "discount amount",
        "discount",
        "discount value",
        "discount sales",
        "sales discount",
        "trade discount",
        "discount given",
    ],

    "cogs": [
        "cogs",
        "cost of goods sold",
        "cost",
        "cost value",
        "product cost",
        "item cost",
        "sales cost",
        "cost of sales",
    ],

    "returns_value": [
        "returns value",
        "return value",
        "returns amount",
        "return amount",
        "sales returns",
        "returned value",
    ],

    "promo_flag": [
        "promo flag",
        "promotion flag",
        "promotion",
        "promo",
        "on promotion",
        "promotion active",
        "promo active",
    ],


    # ========================================================
    # INVENTORY
    # ========================================================

    "opening_stock": [
        "opening stock",
        "opening inventory",
        "beginning stock",
        "beginning inventory",
        "opening balance",
    ],

    "received_units": [
        "received units",
        "received stock",
        "receipts",
        "stock received",
        "inventory received",
        "delivery quantity",
    ],

    "closing_stock": [
        "closing stock",
        "closing inventory",
        "ending stock",
        "ending inventory",
        "closing balance",
        "stock on hand",
        "soh",
    ],

    "stockout_flag": [
        "stockout flag",
        "stock out flag",
        "stockout",
        "stock out",
        "oos flag",
        "oos",
        "out of stock",
        "out of stock flag",
    ],


    # ========================================================
    # TARGETS
    # ========================================================

    "sales_target": [
        "sales target",
        "revenue target",
        "target sales",
        "target revenue",
        "sales goal",
        "revenue goal",
    ],

    "units_target": [
        "units target",
        "volume target",
        "quantity target",
        "target units",
        "target volume",
    ],

    "margin_target_pct": [
        "margin target",
        "margin target pct",
        "margin target percent",
        "gross margin target",
        "target margin",
    ],
}