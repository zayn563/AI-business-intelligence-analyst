-- ============================================================
-- AI BUSINESS INTELLIGENCE ANALYST
-- CORE ANALYTICAL DATABASE SCHEMA
-- ============================================================


-- ============================================================
-- SCHEMA
-- ============================================================

CREATE SCHEMA IF NOT EXISTS analytics;


-- ============================================================
-- DIMENSION: DATE
-- ============================================================

CREATE TABLE IF NOT EXISTS analytics.dim_date (

    date_id DATE PRIMARY KEY,

    year SMALLINT NOT NULL,

    quarter SMALLINT NOT NULL
        CHECK (quarter BETWEEN 1 AND 4),

    month SMALLINT NOT NULL
        CHECK (month BETWEEN 1 AND 12),

    month_name VARCHAR(20) NOT NULL,

    week SMALLINT NOT NULL,

    day_of_month SMALLINT NOT NULL,

    day_of_week SMALLINT NOT NULL
        CHECK (day_of_week BETWEEN 1 AND 7),

    day_name VARCHAR(20) NOT NULL,

    is_weekend BOOLEAN NOT NULL
);


-- ============================================================
-- DIMENSION: STORE
-- ============================================================

CREATE TABLE IF NOT EXISTS analytics.dim_store (

    store_id INTEGER PRIMARY KEY,

    store_name VARCHAR(150) NOT NULL,

    city VARCHAR(100) NOT NULL,

    region VARCHAR(50) NOT NULL,

    channel VARCHAR(100) NOT NULL,

    store_format VARCHAR(100),

    latitude NUMERIC(10,7),

    longitude NUMERIC(10,7),

    opened_date DATE
);


-- ============================================================
-- DIMENSION: PRODUCT
-- ============================================================

CREATE TABLE IF NOT EXISTS analytics.dim_product (

    product_id INTEGER PRIMARY KEY,

    product_name VARCHAR(150) NOT NULL,

    brand VARCHAR(100) NOT NULL,

    category VARCHAR(100) NOT NULL,

    subcategory VARCHAR(100),

    pack_size VARCHAR(50),

    list_price NUMERIC(12,2) NOT NULL
        CHECK (list_price >= 0),

    standard_cost NUMERIC(12,2) NOT NULL
        CHECK (standard_cost >= 0)
);


-- ============================================================
-- DIMENSION: SALESPERSON
-- ============================================================

CREATE TABLE IF NOT EXISTS analytics.dim_salesperson (

    salesperson_id INTEGER PRIMARY KEY,

    salesperson_name VARCHAR(150) NOT NULL,

    region VARCHAR(50) NOT NULL,

    team VARCHAR(100),

    manager_name VARCHAR(150)
);


-- ============================================================
-- FACT: DAILY SALES
-- ============================================================

CREATE TABLE IF NOT EXISTS analytics.fact_sales_daily (

    sales_id BIGSERIAL PRIMARY KEY,

    date_id DATE NOT NULL,

    store_id INTEGER NOT NULL,

    product_id INTEGER NOT NULL,

    salesperson_id INTEGER NOT NULL,

    units_sold INTEGER NOT NULL
        CHECK (units_sold >= 0),

    transactions INTEGER NOT NULL
        CHECK (transactions >= 0),

    gross_sales NUMERIC(14,2) NOT NULL
        CHECK (gross_sales >= 0),

    discount_amount NUMERIC(14,2) NOT NULL
        CHECK (discount_amount >= 0),

    net_sales NUMERIC(14,2) NOT NULL
        CHECK (net_sales >= 0),

    cogs NUMERIC(14,2) NOT NULL
        CHECK (cogs >= 0),

    returns_value NUMERIC(14,2) NOT NULL DEFAULT 0
        CHECK (returns_value >= 0),

    promo_flag BOOLEAN NOT NULL DEFAULT FALSE,

    CONSTRAINT fk_sales_date
        FOREIGN KEY (date_id)
        REFERENCES analytics.dim_date(date_id),

    CONSTRAINT fk_sales_store
        FOREIGN KEY (store_id)
        REFERENCES analytics.dim_store(store_id),

    CONSTRAINT fk_sales_product
        FOREIGN KEY (product_id)
        REFERENCES analytics.dim_product(product_id),

    CONSTRAINT fk_sales_salesperson
        FOREIGN KEY (salesperson_id)
        REFERENCES analytics.dim_salesperson(salesperson_id),

    CONSTRAINT uq_daily_store_product
        UNIQUE (date_id, store_id, product_id)
);


-- ============================================================
-- FACT: DAILY INVENTORY
-- ============================================================

CREATE TABLE IF NOT EXISTS analytics.fact_inventory_daily (

    inventory_id BIGSERIAL PRIMARY KEY,

    date_id DATE NOT NULL,

    store_id INTEGER NOT NULL,

    product_id INTEGER NOT NULL,

    opening_stock INTEGER NOT NULL
        CHECK (opening_stock >= 0),

    received_units INTEGER NOT NULL
        CHECK (received_units >= 0),

    closing_stock INTEGER NOT NULL
        CHECK (closing_stock >= 0),

    stockout_flag BOOLEAN NOT NULL,

    CONSTRAINT fk_inventory_date
        FOREIGN KEY (date_id)
        REFERENCES analytics.dim_date(date_id),

    CONSTRAINT fk_inventory_store
        FOREIGN KEY (store_id)
        REFERENCES analytics.dim_store(store_id),

    CONSTRAINT fk_inventory_product
        FOREIGN KEY (product_id)
        REFERENCES analytics.dim_product(product_id),

    CONSTRAINT uq_inventory_daily_store_product
        UNIQUE (date_id, store_id, product_id)
);


-- ============================================================
-- FACT: MONTHLY TARGETS
-- ============================================================

CREATE TABLE IF NOT EXISTS analytics.fact_targets_monthly (

    target_id BIGSERIAL PRIMARY KEY,

    month_start DATE NOT NULL,

    region VARCHAR(50) NOT NULL,

    category VARCHAR(100) NOT NULL,

    sales_target NUMERIC(14,2) NOT NULL
        CHECK (sales_target >= 0),

    units_target INTEGER NOT NULL
        CHECK (units_target >= 0),

    margin_target_pct NUMERIC(8,4),

    CONSTRAINT uq_target_month_region_category
        UNIQUE (
            month_start,
            region,
            category
        )
);


-- ============================================================
-- FACT: PROMOTIONS
-- ============================================================

CREATE TABLE IF NOT EXISTS analytics.fact_promotions (

    promotion_id INTEGER PRIMARY KEY,

    product_id INTEGER NOT NULL,

    region VARCHAR(50),

    promotion_type VARCHAR(100),

    campaign_name VARCHAR(150),

    start_date DATE NOT NULL,

    end_date DATE NOT NULL,

    discount_pct NUMERIC(8,4)
        CHECK (
            discount_pct >= 0
            AND discount_pct <= 1
        ),

    CONSTRAINT fk_promotion_product
        FOREIGN KEY (product_id)
        REFERENCES analytics.dim_product(product_id),

    CONSTRAINT chk_promotion_dates
        CHECK (end_date >= start_date)
);