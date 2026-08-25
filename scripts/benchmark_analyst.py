import argparse
import json
import statistics
import time
import urllib.error
import urllib.request


# ============================================================
# DEFAULT CONFIGURATION
# ============================================================

DEFAULT_API_URL = (
    "http://127.0.0.1:8000/analyst/ask"
)


QUESTIONS = [
    (
        "Why did North sales decline "
        "in June 2026?"
    ),

    (
        "How did East perform against "
        "target in July 2026?"
    ),

    (
        "Did the April 2026 "
        "promotion work?"
    ),

    (
        "What drove South margin "
        "deterioration in July 2026?"
    ),

    (
        "What are the most important "
        "business issues I should focus on?"
    ),
]


# ============================================================
# HTTP REQUEST
# ============================================================

def ask_question(
    api_url: str,
    question: str,
) -> tuple[
    dict,
    float,
]:

    body = (
        json.dumps(
            {
                "question":
                    question,
            }
        )
        .encode(
            "utf-8"
        )
    )

    request = (
        urllib.request.Request(
            url=
                api_url,

            data=
                body,

            headers={
                "Content-Type":
                    "application/json",
            },

            method=
                "POST",
        )
    )

    started = (
        time.perf_counter()
    )

    with urllib.request.urlopen(
        request,
        timeout=300,
    ) as response:

        raw = (
            response
            .read()
            .decode(
                "utf-8"
            )
        )

    client_ms = (
        (
            time.perf_counter()
            -
            started
        )
        *
        1000
    )

    return (
        json.loads(
            raw
        ),
        round(
            client_ms,
            2,
        ),
    )


# ============================================================
# BENCHMARK
# ============================================================

def run_benchmark(
    api_url: str,
    repeats: int,
):

    timings = []

    print()
    print(
        "="
        *
        72
    )

    print(
        "AI BUSINESS INTELLIGENCE ANALYST "
        "PERFORMANCE BENCHMARK"
    )

    print(
        "="
        *
        72
    )

    print(
        f"API: {api_url}"
    )

    print(
        f"Repeats per question: {repeats}"
    )

    print()

    for question_number, question in enumerate(
        QUESTIONS,
        start=1,
    ):

        print(
            "-"
            *
            72
        )

        print(
            f"QUESTION {question_number}"
        )

        print(
            question
        )

        question_timings = []

        for run_number in range(
            1,
            repeats + 1,
        ):

            try:

                (
                    result,
                    client_ms,
                ) = (
                    ask_question(
                        api_url,
                        question,
                    )
                )

            except urllib.error.URLError as error:

                print()
                print(
                    "ERROR:"
                )

                print(
                    error
                )

                print()
                print(
                    "Make sure FastAPI is running:"
                )

                print(
                    "python -m uvicorn "
                    "backend.app.main:app --reload"
                )

                return

            server_ms = (
                result.get(
                    "response_time_ms"
                )
            )

            parser = (
                result.get(
                    "parser"
                )
            )

            mode = (
                result.get(
                    "execution_mode"
                )
            )

            tool = (
                result.get(
                    "tool_used"
                )
            )

            used_llm = (
                result.get(
                    "used_llm"
                )
            )

            question_timings.append(
                client_ms
            )

            timings.append(
                client_ms
            )

            print()
            print(
                f"Run {run_number}"
            )

            print(
                f"  Client time:     "
                f"{client_ms:,.2f} ms"
            )

            print(
                f"  Server time:     "
                f"{server_ms} ms"
            )

            print(
                f"  Parser:          "
                f"{parser}"
            )

            print(
                f"  Execution mode:  "
                f"{mode}"
            )

            print(
                f"  Tool:            "
                f"{tool}"
            )

            print(
                f"  Local AI used:   "
                f"{used_llm}"
            )

        print()

        print(
            "Question average: "
            f"{statistics.mean(question_timings):,.2f} ms"
        )

    print()
    print(
        "="
        *
        72
    )

    print(
        "SUMMARY"
    )

    print(
        "="
        *
        72
    )

    if timings:

        print(
            "Average: "
            f"{statistics.mean(timings):,.2f} ms"
        )

        print(
            "Median:  "
            f"{statistics.median(timings):,.2f} ms"
        )

        print(
            "Fastest: "
            f"{min(timings):,.2f} ms"
        )

        print(
            "Slowest: "
            f"{max(timings):,.2f} ms"
        )

    print()


# ============================================================
# CLI
# ============================================================

def main():

    parser = (
        argparse.ArgumentParser(
            description=(
                "Benchmark the local AI Business "
                "Intelligence Analyst API."
            )
        )
    )

    parser.add_argument(
        "--api-url",
        default=
            DEFAULT_API_URL,
    )

    parser.add_argument(
        "--repeats",
        type=int,
        default=2,
    )

    args = (
        parser.parse_args()
    )

    run_benchmark(
        api_url=
            args.api_url,

        repeats=
            max(
                1,
                args.repeats,
            ),
    )


if __name__ == "__main__":

    main()