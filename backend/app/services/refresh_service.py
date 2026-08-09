from ..ingestion.hasher import (
    add_record_identity,
)

from ..ingestion.reader import (
    read_source_dataframe,
)

from ..ingestion.sync_service import (
    sync_sales_fact,
)

from ..ingestion.transformer import (
    apply_refresh_mapping_overrides,
    required_mapping_gaps,
    transform_to_sales_fact,
)

from ..ingestion.validator import (
    validate_sales_fact_dataframe,
    validate_source_dataframe,
)

from ..semantic.mapper import (
    map_profile_to_canonical,
)

from ..semantic.profiler import (
    profile_dataset,
)

from ..sources.registry import (
    finish_refresh,
    get_source,
    get_source_mappings,
    replace_source_mappings,
    start_refresh,
    update_source_schema_state,
)

from ..sources.schema_checker import (
    has_schema_changed,
    schema_fingerprint,
)


# ============================================================
# REFRESH A REGISTERED SOURCE
# ============================================================

def refresh_source(
    source_id: int,
) -> dict:

    source = get_source(
        source_id
    )


    if source is None:

        raise KeyError(
            f"Source {source_id} "
            f"does not exist."
        )


    if not source[
        "is_active"
    ]:

        raise ValueError(
            f"Source {source_id} "
            f"is inactive."
        )


    refresh_id = start_refresh(
        source_id
    )


    rows_read = 0

    current_fingerprint = None

    schema_changed = None


    try:

        # ====================================================
        # 1. READ SOURCE
        # ====================================================

        dataframe = (
            read_source_dataframe(
                source
            )
        )


        rows_read = len(
            dataframe
        )


        validate_source_dataframe(
            dataframe
        )


        # ====================================================
        # 2. SCHEMA FINGERPRINT
        # ====================================================

        current_fingerprint = (
            schema_fingerprint(
                list(
                    dataframe.columns
                )
            )
        )


        schema_changed = (
            has_schema_changed(

                source.get(
                    "schema_fingerprint"
                ),

                current_fingerprint,
            )
        )


        # ====================================================
        # 3. MAPPING
        # ====================================================

        saved_mappings = (
            get_source_mappings(
                source_id
            )
        )


        mapping_reused = False


        if (
            not schema_changed
            and saved_mappings
            and source[
                "mapping_status"
            ]
            == "ready"
        ):

            mappings = (
                saved_mappings
            )

            mapping_reused = True


        else:

            profile = profile_dataset(

                columns=list(
                    dataframe.columns
                ),

                sample_rows=(
                    dataframe
                    .head(100)
                    .to_dict(
                        "records"
                    )
                ),
            )


            mapping_result = (
                map_profile_to_canonical(
                    profile
                )
            )


            mapping_result = (
                apply_refresh_mapping_overrides(
                    mapping_result
                )
            )


            mappings = (
                mapping_result[
                    "mappings"
                ]
            )


            replace_source_mappings(
                source_id,
                mappings,
            )


            gaps = (
                required_mapping_gaps(
                    mappings
                )
            )


            if gaps:

                update_source_schema_state(

                    source_id=
                        source_id,

                    fingerprint=
                        current_fingerprint,

                    mapping_status=
                        "review_required",
                )


                raise ValueError(
                    "Source schema cannot yet "
                    "be loaded into the current "
                    "sales warehouse. "
                    "Required canonical mappings "
                    f"missing: {gaps}"
                )


            update_source_schema_state(

                source_id=
                    source_id,

                fingerprint=
                    current_fingerprint,

                mapping_status=
                    "ready",
            )


        # ====================================================
        # 4. TRANSFORM
        # ====================================================

        canonical = (
            transform_to_sales_fact(

                dataframe=
                    dataframe,

                mappings=
                    mappings,
            )
        )


        # ====================================================
        # 5. VALIDATE
        # ====================================================

        validate_sales_fact_dataframe(
            canonical
        )


        # ====================================================
        # 6. RECORD IDENTITY / HASHES
        # ====================================================

        canonical = (
            add_record_identity(
                canonical
            )
        )


        # ====================================================
        # 7. INCREMENTAL SYNC
        # ====================================================

        sync_result = (
            sync_sales_fact(

                dataframe=
                    canonical,

                source_id=
                    source_id,

                load_strategy=
                    source[
                        "load_strategy"
                    ],
            )
        )


        # ====================================================
        # 8. LOG SUCCESS
        # ====================================================

        details = {

            "mapping_reused":
                mapping_reused,

            "schema_fingerprint":
                current_fingerprint,

            "load_strategy":
                source[
                    "load_strategy"
                ],
        }


        finish_refresh(

            refresh_id=
                refresh_id,

            source_id=
                source_id,

            status=
                "success",

            schema_changed=
                schema_changed,

            rows_read=
                sync_result[
                    "rows_read"
                ],

            rows_inserted=
                sync_result[
                    "rows_inserted"
                ],

            rows_updated=
                sync_result[
                    "rows_updated"
                ],

            rows_unchanged=
                sync_result[
                    "rows_unchanged"
                ],

            rows_rejected=
                sync_result[
                    "rows_rejected"
                ],

            details=
                details,
        )


        return {

            "refresh_id":
                refresh_id,

            "source_id":
                source_id,

            "source_name":
                source[
                    "source_name"
                ],

            "status":
                "success",

            "schema_changed":
                schema_changed,

            "mapping_reused":
                mapping_reused,

            **sync_result,
        }


    except Exception as error:

        finish_refresh(

            refresh_id=
                refresh_id,

            source_id=
                source_id,

            status=
                "failed",

            schema_changed=
                schema_changed,

            rows_read=
                rows_read,

            error_message=
                str(
                    error
                ),

            details={
                "schema_fingerprint":
                    current_fingerprint
            },
        )


        raise