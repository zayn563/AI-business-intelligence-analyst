from uuid import uuid4

from .intent_parser import (
    parse_intent,
)

from .response_composer import (
    compose_answer,
)

from .tool_router import (
    route_intent,
)


# ============================================================
# ASK ANALYST
# ============================================================

def ask_analyst(
    question: str,
) -> dict:

    analysis_id = (
        str(
            uuid4()
        )
    )

    # --------------------------------------------------------
    # 1. UNDERSTAND THE QUESTION
    # --------------------------------------------------------

    (
        intent,
        parser_name,
        parser_warnings,
    ) = (
        parse_intent(
            question
        )
    )

    # --------------------------------------------------------
    # 2. CHOOSE AND RUN VERIFIED TOOL
    # --------------------------------------------------------

    tool_result = (
        route_intent(
            intent
        )
    )

    # --------------------------------------------------------
    # 3. EXPLAIN VERIFIED RESULT
    # --------------------------------------------------------

    (
        answer,
        used_llm,
        composer_warnings,
    ) = (
        compose_answer(
            question=
                question,

            intent=
                intent,

            result=
                tool_result,
        )
    )

    warnings = (
        parser_warnings
        +
        composer_warnings
    )

    return {
        "status":
            "success",

        "analysis_id":
            analysis_id,

        "question":
            question,

        "answer":
            answer,

        "intent":
            intent.model_dump(
                mode="json"
            ),

        "parser":
            parser_name,

        "tool_used":
            tool_result[
                "tool"
            ],

        "used_llm":
            used_llm,

        "evidence":
            tool_result.get(
                "data",
                {},
            ),

        "warnings":
            warnings,
    }