from collections import defaultdict
from difflib import SequenceMatcher

import pandas as pd

from .aliases import (
    FIELD_ALIASES,
)

from .canonical_schema import (
    CANONICAL_FIELDS,
    evaluate_capabilities,
)

from .profiler import (
    normalize_header,
)


# ============================================================
# CONFIDENCE THRESHOLDS
# ============================================================

AUTO_MAP_THRESHOLD = 0.90

REVIEW_THRESHOLD = 0.72


# ============================================================
# TYPE COMPATIBILITY
# ============================================================

TYPE_COMPATIBILITY = {

    "date": {
        "date": 1.00,
        "categorical": 0.30,
        "unknown": 0.50,
    },

    "numeric": {
        "numeric": 1.00,
        "integer": 1.00,
        "identifier": 0.35,
        "categorical": 0.20,
        "unknown": 0.50,
    },

    "identifier": {
        "identifier": 1.00,
        "integer": 0.90,
        "numeric": 0.75,
        "categorical": 0.80,
        "unknown": 0.50,
    },

    "categorical": {
        "categorical": 1.00,
        "identifier": 0.80,
        "integer": 0.40,
        "numeric": 0.30,
        "unknown": 0.50,
    },

    "boolean": {
        "boolean": 1.00,
        "categorical": 0.50,
        "integer": 0.40,
        "unknown": 0.50,
    },
}


# ============================================================
# STRING SIMILARITY
# ============================================================

def _name_similarity(
    source: str,
    candidate: str,
) -> float:

    source = normalize_header(
        source
    )

    candidate = normalize_header(
        candidate
    )


    if not source or not candidate:

        return 0.0


    # --------------------------------------------------------
    # Character sequence similarity
    # --------------------------------------------------------

    sequence_score = (
        SequenceMatcher(
            None,
            source,
            candidate,
            autojunk=False,
        )
        .ratio()
    )


    # --------------------------------------------------------
    # Token overlap
    # --------------------------------------------------------

    source_tokens = set(
        source.split(
            "_"
        )
    )

    candidate_tokens = set(
        candidate.split(
            "_"
        )
    )


    union = (
        source_tokens
        | candidate_tokens
    )


    if union:

        token_score = (

            len(
                source_tokens
                & candidate_tokens
            )

            / len(
                union
            )
        )

    else:

        token_score = 0.0


    combined_score = (

        0.75
        * sequence_score

        +

        0.25
        * token_score
    )


    # --------------------------------------------------------
    # Containment bonus
    #
    # Example:
    #
    # net_sales_amount
    # contains
    # net_sales
    # --------------------------------------------------------

    containment_score = 0.0


    if (
        source in candidate
        or candidate in source
    ):

        containment_score = 0.88


    return max(
        sequence_score,
        combined_score,
        containment_score,
    )


# ============================================================
# TYPE SCORE
# ============================================================

def _type_score(
    expected_type: str,
    inferred_type: str,
) -> float:

    return (
        TYPE_COMPATIBILITY
        .get(
            expected_type,
            {}
        )
        .get(
            inferred_type,
            0.25,
        )
    )


# ============================================================
# ALIAS OPTIONS
# ============================================================

def _candidate_names(
    canonical_field: str,
) -> list[str]:

    aliases = (
        FIELD_ALIASES.get(
            canonical_field,
            []
        )
    )


    return [

        canonical_field,

        *aliases,
    ]


# ============================================================
# MAP A SINGLE COLUMN
# ============================================================

def _map_column(
    column_profile: dict,
) -> dict:

    source_column = (
        column_profile[
            "source_column"
        ]
    )

    normalized_source = (
        column_profile[
            "normalized_column"
        ]
    )

    inferred_type = (
        column_profile[
            "inferred_type"
        ]
    )


    best = {

        "canonical_field":
            None,

        "confidence":
            0.0,

        "method":
            "unresolved",

        "matched_name":
            None,

        "expected_type":
            None,
    }


    for (
        canonical_field,
        field_definition,
    ) in CANONICAL_FIELDS.items():

        expected_type = (
            field_definition[
                "expected_type"
            ]
        )


        candidate_names = (
            _candidate_names(
                canonical_field
            )
        )


        normalized_candidates = [

            normalize_header(
                candidate
            )

            for candidate
            in candidate_names
        ]


        # ====================================================
        # LEVEL 1
        # Exact canonical match
        # ====================================================

        if (
            normalized_source
            ==
            normalize_header(
                canonical_field
            )
        ):

            candidate_result = {

                "canonical_field":
                    canonical_field,

                "confidence":
                    1.00,

                "method":
                    "canonical_exact",

                "matched_name":
                    canonical_field,

                "expected_type":
                    expected_type,
            }


        # ====================================================
        # LEVEL 2
        # Exact alias match
        # ====================================================

        elif (
            normalized_source
            in normalized_candidates
        ):

            index = (
                normalized_candidates
                .index(
                    normalized_source
                )
            )


            candidate_result = {

                "canonical_field":
                    canonical_field,

                "confidence":
                    0.97,

                "method":
                    "alias_exact",

                "matched_name":
                    candidate_names[
                        index
                    ],

                "expected_type":
                    expected_type,
            }


        # ====================================================
        # LEVEL 3 + 4
        # Fuzzy name + type compatibility
        # ====================================================

        else:

            best_name = None

            best_name_score = 0.0


            for candidate in (
                candidate_names
            ):

                similarity = (
                    _name_similarity(
                        normalized_source,
                        candidate,
                    )
                )


                if (
                    similarity
                    > best_name_score
                ):

                    best_name_score = (
                        similarity
                    )

                    best_name = (
                        candidate
                    )


            type_score = (
                _type_score(
                    expected_type,
                    inferred_type,
                )
            )


            confidence = (

                0.85
                * best_name_score

                +

                0.15
                * type_score
            )


            # Reserve 0.97+ for exact matches.
            confidence = min(
                confidence,
                0.94,
            )


            # Strong fuzzy name match + sensible type
            # gets minimum automatic confidence.
            if (
                best_name_score >= 0.90
                and type_score >= 0.70
            ):

                confidence = max(
                    confidence,
                    0.90,
                )


            candidate_result = {

                "canonical_field":
                    canonical_field,

                "confidence":
                    confidence,

                "method":
                    "fuzzy",

                "matched_name":
                    best_name,

                "expected_type":
                    expected_type,
            }


        if (
            candidate_result[
                "confidence"
            ]
            >
            best[
                "confidence"
            ]
        ):

            best = (
                candidate_result
            )


    # ========================================================
    # STATUS
    # ========================================================

    confidence = round(
        best["confidence"],
        4,
    )


    if (
        confidence
        >= AUTO_MAP_THRESHOLD
    ):

        status = (
            "auto_mapped"
        )


    elif (
        confidence
        >= REVIEW_THRESHOLD
    ):

        status = (
            "review"
        )


    else:

        status = (
            "unresolved"
        )

        best[
            "canonical_field"
        ] = None


    return {

        "source_column":
            source_column,

        "normalized_column":
            normalized_source,

        "source_type":
            inferred_type,

        "canonical_field":
            best[
                "canonical_field"
            ],

        "expected_type":
            best[
                "expected_type"
            ],

        "confidence":
            confidence,

        "method":
            best[
                "method"
            ],

        "matched_name":
            best[
                "matched_name"
            ],

        "status":
            status,
    }


# ============================================================
# HANDLE COLLISIONS
#
# Two source columns must not silently map to the same
# canonical field.
# ============================================================

def _resolve_collisions(
    mappings: list[dict],
) -> list[dict]:

    grouped = defaultdict(
        list
    )


    for mapping in mappings:

        canonical_field = (
            mapping[
                "canonical_field"
            ]
        )


        if canonical_field:

            grouped[
                canonical_field
            ].append(
                mapping
            )


    for (
        canonical_field,
        candidates,
    ) in grouped.items():

        if len(
            candidates
        ) <= 1:

            continue


        ranked = sorted(

            candidates,

            key=lambda item:
                item[
                    "confidence"
                ],

            reverse=True,
        )


        winner = ranked[0]


        for candidate in (
            ranked[1:]
        ):

            candidate[
                "status"
            ] = (
                "conflict_review"
            )

            candidate[
                "conflict_with"
            ] = (
                winner[
                    "source_column"
                ]
            )


    return mappings


# ============================================================
# DATASET MAPPING
# ============================================================

def map_profile_to_canonical(
    profile: dict,
) -> dict:

    mappings = [

        _map_column(
            column_profile
        )

        for column_profile
        in profile[
            "columns"
        ]
    ]


    mappings = (
        _resolve_collisions(
            mappings
        )
    )


    # --------------------------------------------------------
    # Strict fields
    #
    # Only confident automatic mappings.
    # --------------------------------------------------------

    strict_fields = {

        mapping[
            "canonical_field"
        ]

        for mapping
        in mappings

        if (
            mapping[
                "canonical_field"
            ]
            is not None

            and

            mapping[
                "status"
            ]
            == "auto_mapped"
        )
    }


    # --------------------------------------------------------
    # Potential fields
    #
    # Includes mappings requiring human review.
    # --------------------------------------------------------

    potential_fields = {

        mapping[
            "canonical_field"
        ]

        for mapping
        in mappings

        if (
            mapping[
                "canonical_field"
            ]
            is not None

            and

            mapping[
                "status"
            ]
            in {
                "auto_mapped",
                "review",
            }
        )
    }


    status_counts = defaultdict(
        int
    )


    for mapping in mappings:

        status_counts[
            mapping[
                "status"
            ]
        ] += 1


    review_required = [

        mapping

        for mapping
        in mappings

        if mapping[
            "status"
        ]
        in {
            "review",
            "conflict_review",
            "unresolved",
        }
    ]


    return {

        "summary": {

            "total_columns":
                len(mappings),

            "auto_mapped":
                status_counts[
                    "auto_mapped"
                ],

            "review":
                status_counts[
                    "review"
                ],

            "conflict_review":
                status_counts[
                    "conflict_review"
                ],

            "unresolved":
                status_counts[
                    "unresolved"
                ],

            "strict_compatibility_pct":
                round(
                    100.0
                    * len(strict_fields)
                    / max(
                        len(mappings),
                        1,
                    ),
                    2,
                ),
        },

        "mappings":
            mappings,

        "review_required":
            review_required,

        "strict_capabilities":
            evaluate_capabilities(
                strict_fields
            ),

        "potential_capabilities":
            evaluate_capabilities(
                potential_fields
            ),
    }


# ============================================================
# APPLY MAPPING TO A PANDAS DATAFRAME
#
# This gives us the transformation functionality required for
# future CSV / Google Sheets ingestion.
# ============================================================

def canonicalize_dataframe(
    dataframe: pd.DataFrame,
    mapping_result: dict,
    include_review: bool = False,
) -> pd.DataFrame:

    accepted_statuses = {
        "auto_mapped",
    }


    if include_review:

        accepted_statuses.add(
            "review"
        )


    rename_map = {}


    used_targets = set()


    for mapping in (
        mapping_result[
            "mappings"
        ]
    ):

        canonical_field = (
            mapping[
                "canonical_field"
            ]
        )


        if (
            canonical_field is None

            or

            mapping[
                "status"
            ]
            not in accepted_statuses
        ):

            continue


        if (
            canonical_field
            in used_targets
        ):

            continue


        rename_map[
            mapping[
                "source_column"
            ]
        ] = (
            canonical_field
        )


        used_targets.add(
            canonical_field
        )


    canonical_dataframe = (
        dataframe.rename(
            columns=rename_map
        )
        .copy()
    )


    return (
        canonical_dataframe
    )