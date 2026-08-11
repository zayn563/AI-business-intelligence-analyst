import json
import re

from calendar import monthrange
from datetime import (
    date,
    timedelta,
)

from .llm_client import (
    get_openai_client,
    get_openai_model,
    llm_available,
)

from .models import (
    AnalystIntent,
)

from ..intelligence.snapshot_service import (
    get_max_sales_date,
)


# ============================================================
# MONTHS
# ============================================================

MONTHS = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
}


REGIONS = {
    "north": "North",
    "south": "South",
    "east": "East",
    "west": "West",
    "central": "Central",
}


# ============================================================
# STRUCTURED OUTPUT SCHEMA
# ============================================================

INTENT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,

    "properties": {

        "analysis_type": {
            "type": "string",
            "enum": [
                "latest_changes",
                "diagnostic",
                "targets",
                "promotions",
                "unsupported",
            ],
        },

        "metric": {
            "type": [
                "string",
                "null",
            ],
            "enum": [
                "net_sales",
                "units_sold",
                "transactions",
                "gross_profit",
                "margin_pct",
                "avg_selling_price",
                "discount_pct",
                "cost_per_unit",
                "stockout_rate",
                None,
            ],
        },

        "dimension": {
            "type": [
                "string",
                "null",
            ],
            "enum": [
                "overall",
                "region",
                "city",
                "channel",
                "category",
                "brand",
                "product",
                "store",
                "salesperson",
                None,
            ],
        },

        "dimension_value": {
            "type": [
                "string",
                "null",
            ],
        },

        "current_start": {
            "type": [
                "string",
                "null",
            ],
        },

        "current_end": {
            "type": [
                "string",
                "null",
            ],
        },

        "comparison_start": {
            "type": [
                "string",
                "null",
            ],
        },

        "comparison_end": {
            "type": [
                "string",
                "null",
            ],
        },

        "target_month": {
            "type": [
                "string",
                "null",
            ],
        },

        "promotion_start": {
            "type": [
                "string",
                "null",
            ],
        },

        "promotion_end": {
            "type": [
                "string",
                "null",
            ],
        },

        "confidence": {
            "type": "number",
            "minimum": 0,
            "maximum": 1,
        },
    },

    "required": [
        "analysis_type",
        "metric",
        "dimension",
        "dimension_value",
        "current_start",
        "current_end",
        "comparison_start",
        "comparison_end",
        "target_month",
        "promotion_start",
        "promotion_end",
        "confidence",
    ],
}


# ============================================================
# DATE HELPERS
# ============================================================

def month_period(
    year: int,
    month: int,
) -> tuple[
    date,
    date,
]:

    start = date(
        year,
        month,
        1,
    )

    end = date(
        year,
        month,
        monthrange(
            year,
            month,
        )[1],
    )

    return (
        start,
        end,
    )


def previous_month_period(
    start: date,
) -> tuple[
    date,
    date,
]:

    previous_end = (
        start
        -
        timedelta(
            days=1
        )
    )

    previous_start = date(
        previous_end.year,
        previous_end.month,
        1,
    )

    return (
        previous_start,
        previous_end,
    )


# ============================================================
# MONTH EXTRACTION
# ============================================================

def extract_months(
    question: str,
    default_year: int,
) -> list[
    tuple[
        int,
        int,
    ]
]:

    lowered = (
        question.lower()
    )

    found = []

    for name, month_number in (
        MONTHS.items()
    ):

        pattern = (
            rf"\b{name}\b"
            rf"(?:\s+(\d{{4}}))?"
        )

        for match in re.finditer(
            pattern,
            lowered,
        ):

            year = (
                int(
                    match.group(1)
                )
                if
                match.group(1)
                else
                default_year
            )

            found.append(
                (
                    match.start(),
                    year,
                    month_number,
                )
            )

    found.sort(
        key=lambda item:
            item[0]
    )

    return [
        (
            year,
            month,
        )
        for _position, year, month
        in found
    ]


# ============================================================
# METRIC EXTRACTION
# ============================================================

def detect_metric(
    question: str,
) -> str:

    q = (
        question.lower()
    )

    if (
        "margin"
        in q
    ):
        return "margin_pct"

    if (
        "stockout"
        in q
        or
        "stock-out"
        in q
        or
        "availability"
        in q
    ):
        return "stockout_rate"

    if (
        "discount"
        in q
    ):
        return "discount_pct"

    if (
        "price"
        in q
        or
        "asp"
        in q
        or
        "selling price"
        in q
    ):
        return "avg_selling_price"

    if (
        "unit"
        in q
        or
        "volume"
        in q
    ):
        return "units_sold"

    if (
        "transaction"
        in q
    ):
        return "transactions"

    return "net_sales"


# ============================================================
# DIMENSION EXTRACTION
# ============================================================

def detect_region(
    question: str,
) -> str | None:

    q = (
        question.lower()
    )

    for key, value in (
        REGIONS.items()
    ):

        if (
            re.search(
                rf"\b{key}\b",
                q,
            )
        ):

            return value

    return None


# ============================================================
# FALLBACK PARSER
# ============================================================

def fallback_parse(
    question: str,
) -> AnalystIntent:

    latest_date = (
        get_max_sales_date()
    )

    q = (
        question.lower()
    )

    months = (
        extract_months(
            question,
            latest_date.year,
        )
    )

    region = (
        detect_region(
            question
        )
    )

    metric = (
        detect_metric(
            question
        )
    )

    # --------------------------------------------------------
    # TARGETS
    # --------------------------------------------------------

    if (
        "target"
        in q
        or
        "plan"
        in q
        or
        "quota"
        in q
    ):

        if months:

            year, month = (
                months[0]
            )

        else:

            year = (
                latest_date.year
            )

            month = (
                latest_date.month
            )

        return AnalystIntent(
            analysis_type=
                "targets",

            metric=
                "net_sales",

            dimension=
                "region",

            dimension_value=
                region,

            target_month=
                date(
                    year,
                    month,
                    1,
                ),

            confidence=
                0.85,
        )

    # --------------------------------------------------------
    # PROMOTIONS
    # --------------------------------------------------------

    if (
        "promotion"
        in q
        or
        "campaign"
        in q
        or
        "promo"
        in q
    ):

        if months:

            year, month = (
                months[0]
            )

            (
                promo_start,
                promo_end,
            ) = (
                month_period(
                    year,
                    month,
                )
            )

        else:

            promo_start = date(
                latest_date.year,
                1,
                1,
            )

            promo_end = (
                latest_date
            )

        return AnalystIntent(
            analysis_type=
                "promotions",

            promotion_start=
                promo_start,

            promotion_end=
                promo_end,

            confidence=
                0.85,
        )

    # --------------------------------------------------------
    # LATEST BUSINESS CHANGES
    # --------------------------------------------------------

    latest_phrases = [
        "what changed",
        "latest changes",
        "what needs attention",
        "needs attention",
        "most concerning",
        "most concerned",
        "business issues",
        "business performance",
        "how are we doing",
    ]

    if any(
        phrase in q
        for phrase
        in latest_phrases
    ):

        return AnalystIntent(
            analysis_type=
                "latest_changes",

            confidence=
                0.80,
        )

    # --------------------------------------------------------
    # DIAGNOSTIC
    # --------------------------------------------------------

    diagnostic_terms = [
        "why",
        "driver",
        "decline",
        "declined",
        "drop",
        "dropped",
        "fall",
        "fell",
        "increase",
        "increased",
        "growth",
        "grew",
        "deteriorated",
    ]

    if (
        region is not None
        and
        any(
            term in q
            for term
            in diagnostic_terms
        )
    ):

        if months:

            year, month = (
                months[0]
            )

        else:

            year = (
                latest_date.year
            )

            month = (
                latest_date.month
            )

        (
            current_start,
            current_end,
        ) = (
            month_period(
                year,
                month,
            )
        )

        (
            comparison_start,
            comparison_end,
        ) = (
            previous_month_period(
                current_start
            )
        )

        return AnalystIntent(
            analysis_type=
                "diagnostic",

            metric=
                metric,

            dimension=
                "region",

            dimension_value=
                region,

            current_start=
                current_start,

            current_end=
                current_end,

            comparison_start=
                comparison_start,

            comparison_end=
                comparison_end,

            confidence=
                0.80,
        )

    # --------------------------------------------------------
    # UNSUPPORTED
    # --------------------------------------------------------

    return AnalystIntent(
        analysis_type=
            "unsupported",

        confidence=
            0.30,
    )


# ============================================================
# OPENAI PARSER
# ============================================================

def openai_parse(
    question: str,
) -> AnalystIntent:

    latest_date = (
        get_max_sales_date()
    )

    client = (
        get_openai_client()
    )

    model = (
        get_openai_model()
    )

    instructions = f"""
You are the intent parser for an enterprise business
intelligence application.

The database contains retail commercial data.

The latest available business data date is:
{latest_date.isoformat()}

Interpret relative business periods using the DATA date,
not today's calendar date.

Supported analysis types:

latest_changes
- For questions such as:
  "What changed?"
  "What needs attention?"
  "Which areas are concerning?"

diagnostic
- For questions asking why a KPI changed.
- Example:
  "Why did North sales decline in June 2026?"
- Default comparison should be the immediately preceding
  calendar month unless the user explicitly supplies another
  period.

targets
- For questions about target attainment, plan attainment,
  quota, target misses or target achievement.

promotions
- For questions asking whether a promotion or campaign worked.

unsupported
- Anything outside the supported commercial analytics scope.

Supported regions:
North
South
East
West
Central

Supported metrics:
net_sales
units_sold
transactions
gross_profit
margin_pct
avg_selling_price
discount_pct
cost_per_unit
stockout_rate

Return dates as YYYY-MM-DD.

For a month-level diagnostic:
current_start = first day of requested month
current_end = last day of requested month
comparison = immediately preceding month unless specified.

For target_month:
use the first day of the requested month.

Do not calculate KPIs.
Do not invent evidence.
Only parse the analytical intent.
"""

    response = (
        client.responses.create(
            model=
                model,

            instructions=
                instructions,

            input=
                question,

            text={
                "format": {
                    "type":
                        "json_schema",

                    "name":
                        "analyst_intent",

                    "strict":
                        True,

                    "schema":
                        INTENT_SCHEMA,
                }
            },

            store=
                False,
        )
    )

    payload = json.loads(
        response.output_text
    )

    return (
        AnalystIntent
        .model_validate(
            payload
        )
    )


# ============================================================
# PUBLIC PARSER
# ============================================================

def parse_intent(
    question: str,
    force_fallback: bool = False,
) -> tuple[
    AnalystIntent,
    str,
    list[str],
]:

    warnings = []

    if (
        not force_fallback
        and
        llm_available()
    ):

        try:

            intent = (
                openai_parse(
                    question
                )
            )

            return (
                intent,
                "openai_structured",
                warnings,
            )

        except Exception as error:

            warnings.append(
                "OpenAI intent parsing failed; "
                "deterministic fallback parser was used. "
                f"{type(error).__name__}: {str(error)}"
            )

    intent = (
        fallback_parse(
            question
        )
    )

    return (
        intent,
        "deterministic_fallback",
        warnings,
    )