-- ============================================================
-- SALES FACT INDEXES
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_sales_date
ON analytics.fact_sales_daily(date_id);

CREATE INDEX IF NOT EXISTS idx_sales_store
ON analytics.fact_sales_daily(store_id);

CREATE INDEX IF NOT EXISTS idx_sales_product
ON analytics.fact_sales_daily(product_id);

CREATE INDEX IF NOT EXISTS idx_sales_salesperson
ON analytics.fact_sales_daily(salesperson_id);

CREATE INDEX IF NOT EXISTS idx_sales_date_store
ON analytics.fact_sales_daily(
    date_id,
    store_id
);

CREATE INDEX IF NOT EXISTS idx_sales_date_product
ON analytics.fact_sales_daily(
    date_id,
    product_id
);


-- ============================================================
-- INVENTORY INDEXES
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_inventory_date
ON analytics.fact_inventory_daily(date_id);

CREATE INDEX IF NOT EXISTS idx_inventory_store
ON analytics.fact_inventory_daily(store_id);

CREATE INDEX IF NOT EXISTS idx_inventory_product
ON analytics.fact_inventory_daily(product_id);

CREATE INDEX IF NOT EXISTS idx_inventory_stockout
ON analytics.fact_inventory_daily(stockout_flag);


-- ============================================================
-- TARGET INDEXES
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_targets_month_region
ON analytics.fact_targets_monthly(
    month_start,
    region
);


CREATE INDEX IF NOT EXISTS idx_targets_category
ON analytics.fact_targets_monthly(
    category
);


-- ============================================================
-- STORE DIMENSION
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_store_region
ON analytics.dim_store(region);

CREATE INDEX IF NOT EXISTS idx_store_city
ON analytics.dim_store(city);

CREATE INDEX IF NOT EXISTS idx_store_channel
ON analytics.dim_store(channel);


-- ============================================================
-- PRODUCT DIMENSION
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_product_category
ON analytics.dim_product(category);

CREATE INDEX IF NOT EXISTS idx_product_subcategory
ON analytics.dim_product(subcategory);

CREATE INDEX IF NOT EXISTS idx_product_brand
ON analytics.dim_product(brand);