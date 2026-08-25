import json
import re

from calendar import monthrange
from datetime import (
    date,
    timedelta,
)
from time import monotonic

from ..config import settings

from ..intelligence.snapshot_service import (
    get_max_sales_date,
)

from .llm_client import (
    extract_json_text,
    get_llm_client,
    get_ollama_model,
    llm_available,
)

from .models import (
    AnalystIntent,
)


# ============================================================
# MONTHS
# ============================================================

MONTHS = {
    "january":
        1,

    "february":
        2,

    "march":
        3,

    "april":
        4,

    "may":
        5,

    "june":
        6,

    "july":
        7,

    "august":
        8,

    "september":
        9,

    "october":
        10,

    "november":
        11,

    "december":
        12,
}


# ============================================================
# REGIONS
# ============================================================

REGIONS = {
    "north":
        "North",

    "south":
        "South",

    "east":
        "East",

    "west":
        "West",

    "central":
        "Central",
}


# ============================================================
# LOCAL MODEL ALIASES
# ============================================================

ANALYSIS_TYPE_ALIASES = {
    "decline":
        "diagnostic",

    "growth":
        "diagnostic",

    "driver":
        "diagnostic",

    "drivers":
        "diagnostic",

    "diagnosis":
        "diagnostic",

    "why":
        "diagnostic",

    "target":
        "targets",

    "target_analysis":
        "targets",

    "target_performance":
        "targets",

    "promotion":
        "promotions",

    "promotion_analysis":
        "promotions",

    "campaign":
        "promotions",

    "changes":
        "latest_changes",

    "business_changes":
        "latest_changes",

    "latest":
        "latest_changes",
}


METRIC_ALIASES = {
    "sales":
        "net_sales",

    "revenue":
        "net_sales",

    "net sales":
        "net_sales",

    "net_sales":
        "net_sales",

    "units":
        "units_sold",

    "unit":
        "units_sold",

    "volume":
        "units_sold",

    "units_sold":
        "units_sold",

    "transaction":
        "transactions",

    "transactions":
        "transactions",

    "profit":
        "gross_profit",

    "gross profit":
        "gross_profit",

    "gross_profit":
        "gross_profit",

    "margin":
        "margin_pct",

    "gross margin":
        "margin_pct",

    "margin_pct":
        "margin_pct",

    "price":
        "avg_selling_price",

    "asp":
        "avg_selling_price",

    "average selling price":
        "avg_selling_price",

    "avg_selling_price":
        "avg_selling_price",

    "discount":
        "discount_pct",

    "discount rate":
        "discount_pct",

    "discount_pct":
        "discount_pct",

    "cost":
        "cost_per_unit",

    "cost per unit":
        "cost_per_unit",

    "cost_per_unit":
        "cost_per_unit",

    "stockout":
        "stockout_rate",

    "stock out":
        "stockout_rate",

    "stock-out":
        "stockout_rate",

    "availability":
        "stockout_rate",

    "stockout_rate":
        "stockout_rate",
}


DIMENSION_ALIASES = {
    "region":
        "region",

    "regions":
        "region",

    "city":
        "city",

    "cities":
        "city",

    "channel":
        "channel",

    "channels":
        "channel",

    "category":
        "category",

    "categories":
        "category",

    "brand":
        "brand",

    "brands":
        "brand",

    "product":
        "product",

    "products":
        "product",

    "store":
        "store",

    "stores":
        "store",

    "outlet":
        "store",

    "outlets":
        "store",

    "salesperson":
        "salesperson",

    "salespeople":
        "salesperson",

    "overall":
        "overall",
}


# ============================================================
# LATEST DATA DATE CACHE
# ============================================================

_LATEST_DATE_CACHE = {
    "value":
        None,

    "expires_at":
        0.0,
}


LATEST_DATE_CACHE_SECONDS = 60.0


def get_latest_data_date() -> date:

    now = (
        monotonic()
    )

    cached_value = (
        _LATEST_DATE_CACHE[
            "value"
        ]
    )

    cached_until = (
        _LATEST_DATE_CACHE[
            "expires_at"
        ]
    )

    if (
        cached_value is not None
        and
        now
        <
        cached_until
    ):

        return cached_value


    latest_date = (
        get_max_sales_date()
    )

    _LATEST_DATE_CACHE[
        "value"
    ] = (
        latest_date
    )

    _LATEST_DATE_CACHE[
        "expires_at"
    ] = (
        now
        +
        LATEST_DATE_CACHE_SECONDS
    )

    return latest_date


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


def explicit_year(
    question: str,
) -> int | None:

    match = re.search(
        r"\b(20\d{2})\b",
        question,
    )

    if not match:

        return None

    return int(
        match.group(1)
    )


def default_year_for_question(
    question: str,
) -> int:

    year = (
        explicit_year(
            question
        )
    )

    if year is not None:

        return year

    return (
        get_latest_data_date()
        .year
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
        key=
            lambda item:
                item[
                    0
                ]
    )

    return [
        (
            year,
            month,
        )
        for (
            _position,
            year,
            month,
        )
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

        return (
            "margin_pct"
        )

    if (
        "stockout"
        in q
        or
        "stock-out"
        in q
        or
        "stock out"
        in q
        or
        "availability"
        in q
    ):

        return (
            "stockout_rate"
        )

    if (
        "discount"
        in q
    ):

        return (
            "discount_pct"
        )

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

        return (
            "avg_selling_price"
        )

    if (
        "unit"
        in q
        or
        "volume"
        in q
    ):

        return (
            "units_sold"
        )

    if (
        "transaction"
        in q
    ):

        return (
            "transactions"
        )

    if (
        "gross profit"
        in q
        or
        "profit"
        in q
    ):

        return (
            "gross_profit"
        )

    return (
        "net_sales"
    )


# ============================================================
# REGION EXTRACTION
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

        if re.search(
            rf"\b{key}\b",
            q,
        ):

            return value

    return None


# ============================================================
# DETERMINISTIC PARSER
# ============================================================

def fallback_parse(
    question: str,
) -> AnalystIntent:

    q = (
        question.lower()
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
        "quota"
        in q
        or
        "against plan"
        in q
    ):

        default_year = (
            default_year_for_question(
                question
            )
        )

        months = (
            extract_months(
                question,
                default_year,
            )
        )

        if months:

            year, month = (
                months[
                    0
                ]
            )

        else:

            latest_date = (
                get_latest_data_date()
            )

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
                0.95,
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

        default_year = (
            default_year_for_question(
                question
            )
        )

        months = (
            extract_months(
                question,
                default_year,
            )
        )

        if months:

            year, month = (
                months[
                    0
                ]
            )

            (
                promotion_start,
                promotion_end,
            ) = (
                month_period(
                    year,
                    month,
                )
            )

        else:

            latest_date = (
                get_latest_data_date()
            )

            promotion_start = date(
                latest_date.year,
                1,
                1,
            )

            promotion_end = (
                latest_date
            )

        return AnalystIntent(
            analysis_type=
                "promotions",

            promotion_start=
                promotion_start,

            promotion_end=
                promotion_end,

            confidence=
                0.95,
        )


    # --------------------------------------------------------
    # EXECUTIVE / LATEST BUSINESS CHANGES
    # --------------------------------------------------------

    latest_phrases = [
        "what changed",
        "latest changes",
        "what needs attention",
        "needs attention",
        "most concerning",
        "most concerned",
        "business issues",
        "important business issues",
        "business performance",
        "how are we doing",
        "focus on",
        "priorities",
        "priority issues",
        "biggest issues",
    ]

    if any(
        phrase
        in
        q
        for phrase
        in
        latest_phrases
    ):

        return AnalystIntent(
            analysis_type=
                "latest_changes",

            confidence=
                0.90,
        )


    # --------------------------------------------------------
    # DIAGNOSTIC
    # --------------------------------------------------------

    diagnostic_terms = [
        "why",
        "driver",
        "drivers",
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
        "deterioration",
        "improved",
        "improvement",
        "what drove",
        "what caused",
    ]

    if (
        region is not None
        and
        any(
            term
            in
            q
            for term
            in
            diagnostic_terms
        )
    ):

        default_year = (
            default_year_for_question(
                question
            )
        )

        months = (
            extract_months(
                question,
                default_year,
            )
        )

        if months:

            year, month = (
                months[
                    0
                ]
            )

        else:

            latest_date = (
                get_latest_data_date()
            )

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
                0.95,
        )


    # --------------------------------------------------------
    # UNSUPPORTED / AMBIGUOUS
    # --------------------------------------------------------

    return AnalystIntent(
        analysis_type=
            "unsupported",

        confidence=
            0.25,
    )


# ============================================================
# LOCAL MODEL PAYLOAD NORMALIZATION
# ============================================================

def normalize_ollama_intent_payload(
    payload: dict,
) -> dict:

    normalized = dict(
        payload
    )


    # --------------------------------------------------------
    # ANALYSIS TYPE
    # --------------------------------------------------------

    analysis_type = (
        normalized.get(
            "analysis_type"
        )
    )

    if isinstance(
        analysis_type,
        str,
    ):

        key = (
            analysis_type
            .strip()
            .lower()
            .replace(
                "-",
                "_",
            )
        )

        normalized[
            "analysis_type"
        ] = (
            ANALYSIS_TYPE_ALIASES.get(
                key,
                key,
            )
        )


    # --------------------------------------------------------
    # METRIC
    # --------------------------------------------------------

    metric = (
        normalized.get(
            "metric"
        )
    )

    if isinstance(
        metric,
        str,
    ):

        key = (
            metric
            .strip()
            .lower()
            .replace(
                "-",
                " ",
            )
        )

        normalized[
            "metric"
        ] = (
            METRIC_ALIASES.get(
                key,
                metric,
            )
        )


    # --------------------------------------------------------
    # DIMENSION
    # --------------------------------------------------------

    dimension = (
        normalized.get(
            "dimension"
        )
    )

    if isinstance(
        dimension,
        str,
    ):

        key = (
            dimension
            .strip()
            .lower()
        )

        normalized[
            "dimension"
        ] = (
            DIMENSION_ALIASES.get(
                key,
                key,
            )
        )


    # --------------------------------------------------------
    # REGION VALUE
    # --------------------------------------------------------

    if (
        normalized.get(
            "dimension"
        )
        ==
        "region"
    ):

        dimension_value = (
            normalized.get(
                "dimension_value"
            )
        )

        if isinstance(
            dimension_value,
            str,
        ):

            region_key = (
                dimension_value
                .strip()
                .lower()
            )

            normalized[
                "dimension_value"
            ] = (
                REGIONS.get(
                    region_key,
                    dimension_value.strip(),
                )
            )

    return normalized


# ============================================================
# HYBRID ENRICHMENT
# ============================================================

def enrich_local_intent(
    question: str,
    local_intent: AnalystIntent,
) -> AnalystIntent:

    deterministic = (
        fallback_parse(
            question
        )
    )

    local_data = (
        local_intent.model_dump()
    )

    deterministic_data = (
        deterministic.model_dump()
    )


    # --------------------------------------------------------
    # FILL SAFE DETERMINISTIC FIELDS
    # --------------------------------------------------------

    fields_to_enrich = [
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
    ]

    for field_name in (
        fields_to_enrich
    ):

        if (
            local_data.get(
                field_name
            )
            is None
            and
            deterministic_data.get(
                field_name
            )
            is not None
        ):

            local_data[
                field_name
            ] = (
                deterministic_data[
                    field_name
                ]
            )


    # --------------------------------------------------------
    # DIAGNOSTIC DEFAULT METRIC
    # --------------------------------------------------------

    if (
        local_data.get(
            "analysis_type"
        )
        ==
        "diagnostic"
        and
        local_data.get(
            "metric"
        )
        is None
    ):

        local_data[
            "metric"
        ] = (
            detect_metric(
                question
            )
        )


    return (
        AnalystIntent
        .model_validate(
            local_data
        )
    )


# ============================================================
# OLLAMA STRUCTURED PARSER
# ============================================================

def ollama_parse(
    question: str,
) -> AnalystIntent:

    latest_date = (
        get_latest_data_date()
    )

    client = (
        get_llm_client()
    )

    model = (
        get_ollama_model()
    )

    instructions = f"""
You are the intent parser for an enterprise business
intelligence application.

Latest available business-data date:
{latest_date.isoformat()}

Use the data date above rather than today's calendar date
when interpreting relative periods.

Return structured data matching the supplied JSON schema.

Allowed analysis_type values:

latest_changes
diagnostic
targets
promotions
unsupported

Allowed metric values:

net_sales
units_sold
transactions
gross_profit
margin_pct
avg_selling_price
discount_pct
cost_per_unit
stockout_rate

Allowed dimension values:

overall
region
city
channel
category
brand
product
store
salesperson

Example:

Question:
Why did North sales decline in June 2026?

Result:

analysis_type = diagnostic
metric = net_sales
dimension = region
dimension_value = North
current_start = 2026-06-01
current_end = 2026-06-30
comparison_start = 2026-05-01
comparison_end = 2026-05-31

Rules:

1. Never calculate KPIs.
2. Never invent business evidence.
3. Do not explain your reasoning.
4. Return only structured intent.
5. For monthly diagnostics, compare against the immediately
   preceding calendar month unless another comparison is
   explicitly requested.
"""

    response = (
        client.chat(
            model=
                model,

            messages=[
                {
                    "role":
                        "system",

                    "content":
                        instructions,
                },

                {
                    "role":
                        "user",

                    "content":
                        question,
                },
            ],

            format=
                AnalystIntent
                .model_json_schema(),

            options={
                "temperature":
                    0,
            },

            think=
                False,

            stream=
                False,
        )
    )

    content = (
        extract_json_text(
            response.message.content
        )
    )

    payload = (
        json.loads(
            content
        )
    )

    normalized_payload = (
        normalize_ollama_intent_payload(
            payload
        )
    )

    intent = (
        AnalystIntent
        .model_validate(
            normalized_payload
        )
    )

    return (
        enrich_local_intent(
            question,
            intent,
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


    # --------------------------------------------------------
    # FIRST: FAST DETERMINISTIC PARSER
    # --------------------------------------------------------

    deterministic_intent = (
        fallback_parse(
            question
        )
    )


    # --------------------------------------------------------
    # TEST / EXPLICIT FALLBACK MODE
    # --------------------------------------------------------

    if force_fallback:

        return (
            deterministic_intent,
            "deterministic_fallback",
            warnings,
        )


    # --------------------------------------------------------
    # FAST PATH
    #
    # Standard supported business questions never wake Qwen.
    # --------------------------------------------------------

    if (
        deterministic_intent.analysis_type
        !=
        "unsupported"
        and
        deterministic_intent.confidence
        >=
        settings.analyst_fast_path_confidence
    ):

        return (
            deterministic_intent,
            "deterministic_fast_path",
            warnings,
        )


    # --------------------------------------------------------
    # AMBIGUOUS QUESTION:
    # ASK LOCAL QWEN
    # --------------------------------------------------------

    if llm_available():

        try:

            local_intent = (
                ollama_parse(
                    question
                )
            )

            return (
                local_intent,
                "ollama_structured",
                warnings,
            )

        except Exception as error:

            warnings.append(
                (
                    "Local Ollama intent parsing failed; "
                    "the deterministic parser was used. "
                    f"{type(error).__name__}: "
                    f"{str(error)}"
                )
            )


    # --------------------------------------------------------
    # GRACEFUL FALLBACK
    # --------------------------------------------------------

    return (
        deterministic_intent,
        "deterministic_fallback",
        warnings,
    )