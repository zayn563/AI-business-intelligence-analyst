from datetime import (
    date,
    timedelta,
)

from sqlalchemy import text

from ..database import engine


# ============================================================
# HELPERS
# ============================================================

def pct_change(
    current,
    previous,
):

    if (
        current is None
        or
        previous is None
        or
        previous == 0
    ):
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


def delta(
    current,
    previous,
):

    if (
        current is None
        or
        previous is None
    ):
        return None

    return (
        current
        -
        previous
    )


def rounded(
    value,
):

    if value is None:
        return None

    return round(
        float(value),
        2,
    )


# ============================================================
# CLASSIFICATION
# ============================================================

def classify_promotion_performance(
    units_uplift_pct,
    revenue_uplift_pct,
    discount_change_pp,
) -> dict:

    # Strong promotional response:
    # material volume uplift together with
    # meaningfully higher discount intensity.
    if (
        units_uplift_pct
        is not None
        and
        units_uplift_pct
        >=
        10
        and
        discount_change_pp
        is not None
        and
        discount_change_pp
        >=
        5
    ):

        return {
            "diagnosis":
                "promotion_led_volume_growth",

            "effectiveness":
                "strong",

            "severity":
                "high",

            "confidence":
                "high",
        }

    # Volume improved materially,
    # but discount evidence is weaker.
    if (
        units_uplift_pct
        is not None
        and
        units_uplift_pct
        >=
        10
    ):

        return {
            "diagnosis":
                "volume_growth",

            "effectiveness":
                "positive",

            "severity":
                "medium",

            "confidence":
                "high",
        }

    # Revenue improved but volume response
    # was not large enough for a strong
    # promotional conclusion.
    if (
        revenue_uplift_pct
        is not None
        and
        revenue_uplift_pct
        >
        0
    ):

        return {
            "diagnosis":
                "limited_revenue_response",

            "effectiveness":
                "moderate",

            "severity":
                "low",

            "confidence":
                "medium",
        }

    return {
        "diagnosis":
            "weak_or_negative_response",

        "effectiveness":
            "weak",

        "severity":
            "medium",

        "confidence":
            "medium",
    }


# ============================================================
# PROMOTION LIST
# ============================================================

def fetch_promotions(
    start_date: date,
    end_date: date,
) -> list[dict]:

    query = text(
        """
        SELECT
            pr.promotion_id,
            pr.product_id,

            p.product_name,
            p.brand,
            p.category,

            pr.region,
            pr.promotion_type,
            pr.campaign_name,

            pr.start_date,
            pr.end_date,

            pr.discount_pct::double precision
                AS planned_discount_pct

        FROM
            analytics.fact_promotions pr

        JOIN
            analytics.dim_product p
            ON
            pr.product_id
            =
            p.product_id

        WHERE
            pr.start_date
            <=
            :end_date

            AND

            pr.end_date
            >=
            :start_date

        ORDER BY
            pr.start_date,
            pr.promotion_id;
        """
    )

    with engine.connect() as connection:

        rows = (
            connection
            .execute(
                query,
                {
                    "start_date":
                        start_date,

                    "end_date":
                        end_date,
                },
            )
            .mappings()
            .all()
        )

    return [
        dict(row)
        for row in rows
    ]


# ============================================================
# PERIOD PERFORMANCE
# ============================================================

def fetch_product_performance(
    product_id: int,
    start_date: date,
    end_date: date,
    region: str | None,
) -> dict:

    # --------------------------------------------------------
    # IMPORTANT
    #
    # Do not use:
    #
    # (:region IS NULL OR s.region = :region)
    #
    # because PostgreSQL cannot always infer
    # the datatype of a NULL bind parameter.
    #
    # Instead, add the regional filter only
    # when an actual region exists.
    # --------------------------------------------------------

    region_filter = ""

    parameters = {
        "product_id":
            product_id,

        "start_date":
            start_date,

        "end_date":
            end_date,
    }

    if (
        region is not None
        and
        str(region).strip()
        !=
        ""
    ):

        region_filter = """
            AND
                s.region
                =
                :region
        """

        parameters[
            "region"
        ] = region

    sql = f"""
        SELECT
            COALESCE(
                SUM(
                    f.units_sold
                ),
                0
            )::double precision
                AS units_sold,

            COALESCE(
                SUM(
                    f.gross_sales
                ),
                0
            )::double precision
                AS gross_sales,

            COALESCE(
                SUM(
                    f.net_sales
                ),
                0
            )::double precision
                AS net_sales,

            COALESCE(
                SUM(
                    f.discount_amount
                ),
                0
            )::double precision
                AS discount_amount,

            (
                SUM(
                    f.net_sales
                )
                /
                NULLIF(
                    SUM(
                        f.units_sold
                    ),
                    0
                )
            )::double precision
                AS avg_selling_price,

            (
                100.0
                *
                SUM(
                    f.discount_amount
                )
                /
                NULLIF(
                    SUM(
                        f.gross_sales
                    ),
                    0
                )
            )::double precision
                AS discount_pct

        FROM
            analytics.fact_sales_daily f

        JOIN
            analytics.dim_store s
            ON
            f.store_id
            =
            s.store_id

        WHERE
            f.product_id
            =
            :product_id

            AND

            f.date_id
            BETWEEN
            :start_date
            AND
            :end_date

            {region_filter};
    """

    query = text(
        sql
    )

    with engine.connect() as connection:

        row = (
            connection
            .execute(
                query,
                parameters,
            )
            .mappings()
            .one()
        )

    return dict(
        row
    )


# ============================================================
# PROMOTION ANALYSIS
# ============================================================

def analyze_promotions(
    start_date: date,
    end_date: date,
) -> dict:

    if (
        start_date
        >
        end_date
    ):

        raise ValueError(
            "start_date cannot be after end_date."
        )

    promotions = (
        fetch_promotions(
            start_date,
            end_date,
        )
    )

    results = []

    for promotion in promotions:

        promo_start = (
            promotion[
                "start_date"
            ]
        )

        promo_end = (
            promotion[
                "end_date"
            ]
        )

        duration_days = (
            promo_end
            -
            promo_start
        ).days + 1

        # ----------------------------------------------------
        # BASELINE
        #
        # Compare the campaign with the immediately
        # preceding period of equal length.
        # ----------------------------------------------------

        baseline_end = (
            promo_start
            -
            timedelta(
                days=1
            )
        )

        baseline_start = (
            baseline_end
            -
            timedelta(
                days=
                    duration_days
                    -
                    1
            )
        )

        region = (
            promotion.get(
                "region"
            )
        )

        # Normalize blank values to None.
        if (
            region is not None
            and
            str(region).strip()
            ==
            ""
        ):

            region = None

        # ----------------------------------------------------
        # PROMOTION PERIOD PERFORMANCE
        # ----------------------------------------------------

        current = (
            fetch_product_performance(
                product_id=
                    promotion[
                        "product_id"
                    ],

                start_date=
                    promo_start,

                end_date=
                    promo_end,

                region=
                    region,
            )
        )

        # ----------------------------------------------------
        # BASELINE PERFORMANCE
        # ----------------------------------------------------

        baseline = (
            fetch_product_performance(
                product_id=
                    promotion[
                        "product_id"
                    ],

                start_date=
                    baseline_start,

                end_date=
                    baseline_end,

                region=
                    region,
            )
        )

        # ----------------------------------------------------
        # KPI CHANGES
        # ----------------------------------------------------

        units_uplift = (
            pct_change(
                current.get(
                    "units_sold"
                ),
                baseline.get(
                    "units_sold"
                ),
            )
        )

        revenue_uplift = (
            pct_change(
                current.get(
                    "net_sales"
                ),
                baseline.get(
                    "net_sales"
                ),
            )
        )

        asp_change = (
            pct_change(
                current.get(
                    "avg_selling_price"
                ),
                baseline.get(
                    "avg_selling_price"
                ),
            )
        )

        discount_change = (
            delta(
                current.get(
                    "discount_pct"
                ),
                baseline.get(
                    "discount_pct"
                ),
            )
        )

        classification = (
            classify_promotion_performance(
                units_uplift_pct=
                    units_uplift,

                revenue_uplift_pct=
                    revenue_uplift,

                discount_change_pp=
                    discount_change,
            )
        )

        results.append(
            {
                "promotion_id":
                    promotion[
                        "promotion_id"
                    ],

                "campaign_name":
                    promotion[
                        "campaign_name"
                    ],

                "promotion_type":
                    promotion[
                        "promotion_type"
                    ],

                "product_id":
                    promotion[
                        "product_id"
                    ],

                "product_name":
                    promotion[
                        "product_name"
                    ],

                "brand":
                    promotion[
                        "brand"
                    ],

                "category":
                    promotion[
                        "category"
                    ],

                "region":
                    (
                        region
                        if
                        region is not None
                        else
                        "All Regions"
                    ),

                "promotion_period": {
                    "start":
                        promo_start
                        .isoformat(),

                    "end":
                        promo_end
                        .isoformat(),
                },

                "baseline_period": {
                    "start":
                        baseline_start
                        .isoformat(),

                    "end":
                        baseline_end
                        .isoformat(),
                },

                "planned_discount_pct":
                    rounded(
                        float(
                            promotion[
                                "planned_discount_pct"
                            ]
                        )
                        *
                        100.0
                    ),

                "current": {
                    key:
                        rounded(
                            value
                        )
                    for key, value
                    in current.items()
                },

                "baseline": {
                    key:
                        rounded(
                            value
                        )
                    for key, value
                    in baseline.items()
                },

                "units_uplift_pct":
                    rounded(
                        units_uplift
                    ),

                "revenue_uplift_pct":
                    rounded(
                        revenue_uplift
                    ),

                "asp_change_pct":
                    rounded(
                        asp_change
                    ),

                "discount_change_pp":
                    rounded(
                        discount_change
                    ),

                **classification,
            }
        )


    # ========================================================
    # SUMMARY
    # ========================================================

    strong_promotions = sum(
        1
        for row
        in results
        if row[
            "effectiveness"
        ]
        ==
        "strong"
    )

    weak_promotions = sum(
        1
        for row
        in results
        if row[
            "effectiveness"
        ]
        ==
        "weak"
    )


    return {
        "status":
            "success",

        "analysis_type":
            "promotion_effectiveness",

        "analysis_period": {
            "start":
                start_date.isoformat(),

            "end":
                end_date.isoformat(),
        },

        "promotions_evaluated":
            len(
                results
            ),

        "summary": {
            "promotions_evaluated":
                len(
                    results
                ),

            "strong_promotions":
                strong_promotions,

            "weak_promotions":
                weak_promotions,
        },

        "results":
            results,
    }