from sqlalchemy import text

from .metrics import (
    SALES_METRICS,
    SALES_DIMENSIONS,
    SALES_FILTERS,
)

from .schemas import (
    AnalysisRequest,
)


# ============================================================
# BASE SALES QUERY
# ============================================================

BASE_FROM = """

FROM analytics.fact_sales_daily f

JOIN analytics.dim_store s
    ON f.store_id = s.store_id

JOIN analytics.dim_product p
    ON f.product_id = p.product_id

JOIN analytics.dim_salesperson sp
    ON f.salesperson_id = sp.salesperson_id

"""


# ============================================================
# BUILD QUERY
# ============================================================

def build_sales_query(
    request: AnalysisRequest,
    start_date=None,
    end_date=None,
    force_summary=False,
):

    # --------------------------------------------------------
    # PERIOD
    # --------------------------------------------------------

    start_date = (
        start_date
        or request.period.start
    )

    end_date = (
        end_date
        or request.period.end
    )


    params = {

        "start_date":
            start_date,

        "end_date":
            end_date,
    }


    # --------------------------------------------------------
    # SELECT METRICS
    # --------------------------------------------------------

    metric_parts = []


    for metric in request.metrics:

        expression = (
            SALES_METRICS[
                metric
            ][
                "expression"
            ]
        )

        metric_parts.append(
            f"""
            ROUND(
                ({expression})::numeric,
                2
            ) AS {metric}
            """
        )


    # --------------------------------------------------------
    # DIMENSION
    # --------------------------------------------------------

    dimension_expression = None


    if (
        request.dimension
        and not force_summary
    ):

        dimension_expression = (
            SALES_DIMENSIONS[
                request.dimension
            ]
        )


        select_sql = (

            f"""
            {dimension_expression}
                AS dimension,

            """

            +

            ", ".join(
                metric_parts
            )
        )

    else:

        select_sql = ", ".join(
            metric_parts
        )


    # --------------------------------------------------------
    # WHERE CONDITIONS
    # --------------------------------------------------------

    conditions = [

        """
        f.date_id
        BETWEEN :start_date
        AND :end_date
        """

    ]


    filters = (
        request.filters
        .model_dump(
            exclude_none=True
        )
    )


    for filter_name, value in (
        filters.items()
    ):

        column = (
            SALES_FILTERS[
                filter_name
            ]
        )


        parameter_name = (
            f"filter_{filter_name}"
        )


        conditions.append(

            f"""
            {column}
            = :{parameter_name}
            """
        )


        params[
            parameter_name
        ] = value


    # --------------------------------------------------------
    # BUILD SQL
    # --------------------------------------------------------

    sql = f"""

        SELECT

            {select_sql}

        {BASE_FROM}

        WHERE

            {" AND ".join(conditions)}

    """


    # --------------------------------------------------------
    # GROUP BY DIMENSION
    # --------------------------------------------------------

    if dimension_expression:

        sql += f"""

            GROUP BY
                {dimension_expression}

        """


    # --------------------------------------------------------
    # SORTING
    # --------------------------------------------------------

    if (
        request.analysis_type.value
        in {
            "ranking",
            "breakdown",
        }

        and dimension_expression
    ):

        first_metric = (
            request.metrics[0]
        )


        direction = (
            request.sort_direction
            .upper()
        )


        sql += f"""

            ORDER BY
                {first_metric}
                {direction}

        """


    elif (
        request.analysis_type.value
        == "trend"

        and dimension_expression
    ):

        sql += """

            ORDER BY
                dimension ASC

        """


    # --------------------------------------------------------
    # TOP N
    # --------------------------------------------------------

    if (
        request.analysis_type.value
        == "ranking"
    ):

        sql += """

            LIMIT :top_n

        """

        params[
            "top_n"
        ] = request.top_n


    return (
        text(sql),
        params,
    )