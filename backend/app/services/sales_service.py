from datetime import date
from decimal import Decimal

from . import __init__

from ..database import engine

from ..query_builder import (
    build_sales_query,
)

from ..schemas import (
    AnalysisRequest,
)


# ============================================================
# JSON-SAFE SERIALIZATION
# ============================================================

def serialize_value(
    value
):

    if isinstance(
        value,
        Decimal
    ):

        return float(
            value
        )


    if isinstance(
        value,
        date
    ):

        return value.isoformat()


    return value


def serialize_row(
    row
):

    return {

        key:
            serialize_value(
                value
            )

        for key, value
        in row.items()
    }


# ============================================================
# EXECUTE QUERY
# ============================================================

def execute_query(
    statement,
    parameters,
):

    with engine.connect() as connection:

        result = connection.execute(
            statement,
            parameters,
        )

        rows = (
            result
            .mappings()
            .all()
        )


    return [

        serialize_row(
            row
        )

        for row in rows
    ]


# ============================================================
# RUN ANALYSIS
# ============================================================

def run_sales_analysis(
    request: AnalysisRequest,
):


    # ========================================================
    # COMPARISON
    # ========================================================

    if (
        request.analysis_type.value
        == "comparison"
    ):

        current_statement, current_params = (
            build_sales_query(

                request=request,

                start_date=
                    request.period.start,

                end_date=
                    request.period.end,

                force_summary=True,
            )
        )


        comparison_statement, comparison_params = (
            build_sales_query(

                request=request,

                start_date=
                    request.comparison_period.start,

                end_date=
                    request.comparison_period.end,

                force_summary=True,
            )
        )


        current_rows = execute_query(
            current_statement,
            current_params,
        )


        comparison_rows = execute_query(
            comparison_statement,
            comparison_params,
        )


        current = (
            current_rows[0]
            if current_rows
            else {}
        )


        previous = (
            comparison_rows[0]
            if comparison_rows
            else {}
        )


        changes = {}


        for metric in request.metrics:

            current_value = (
                current.get(
                    metric
                )
            )

            previous_value = (
                previous.get(
                    metric
                )
            )


            if (
                current_value is not None
                and previous_value
                not in {
                    None,
                    0,
                }
            ):

                change_pct = (

                    (
                        current_value
                        - previous_value
                    )

                    /
                    previous_value

                    * 100
                )


                changes[
                    metric
                ] = round(
                    change_pct,
                    2,
                )


            else:

                changes[
                    metric
                ] = None


        return {

            "analysis_type":
                "comparison",

            "current_period": {
                "start":
                    request.period.start,
                "end":
                    request.period.end,
            },

            "comparison_period": {
                "start":
                    request.comparison_period.start,
                "end":
                    request.comparison_period.end,
            },

            "current":
                current,

            "comparison":
                previous,

            "change_pct":
                changes,
        }


    # ========================================================
    # NORMAL QUERY
    # ========================================================

    statement, parameters = (
        build_sales_query(
            request
        )
    )


    rows = execute_query(
        statement,
        parameters,
    )


    return {

        "analysis_type":
            request.analysis_type.value,

        "period": {
            "start":
                request.period.start,

            "end":
                request.period.end,
        },

        "dimension":
            request.dimension,

        "metrics":
            request.metrics,

        "filters":
            request.filters.model_dump(
                exclude_none=True
            ),

        "result":
            rows,
    }