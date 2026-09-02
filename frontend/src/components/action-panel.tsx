"use client";

import {
    useCallback,
    useEffect,
    useState,
} from "react";


// ============================================================
// TYPES
// ============================================================

type ActionStatus =
    | "OPEN"
    | "IN_PROGRESS"
    | "BLOCKED"
    | "COMPLETED";


type InsightAction = {

    action_id:
        number;

    insight_id:
        number;

    title:
        string;

    owner_name:
        string | null;

    status:
        ActionStatus;

    due_date:
        string | null;

    notes:
        string | null;

    created_at:
        string;

    updated_at:
        string;

    completed_at:
        string | null;
};


type UnknownRecord =
    Record<
        string,
        unknown
    >;


type Props = {

    insightId:
        number;
};


// ============================================================
// GENERIC HELPERS
// ============================================================

function isRecord(
    value:
        unknown,
): value is UnknownRecord {

    return (
        typeof value
        ===
        "object"
        &&
        value
        !==
        null
        &&
        !Array.isArray(
            value,
        )
    );
}


// ============================================================
// ACTION STATUS
// ============================================================

function isActionStatus(
    value:
        unknown,
): value is ActionStatus {

    return (
        value
        ===
        "OPEN"
        ||
        value
        ===
        "IN_PROGRESS"
        ||
        value
        ===
        "BLOCKED"
        ||
        value
        ===
        "COMPLETED"
    );
}


function parseActionStatus(
    value:
        string,
): ActionStatus | null {

    if (
        isActionStatus(
            value,
        )
    ) {

        return value;
    }


    return null;
}


// ============================================================
// ACTION RECORD PARSER
// ============================================================

function parseInsightAction(
    value:
        unknown,
): InsightAction | null {

    if (
        !isRecord(
            value,
        )
    ) {

        return null;
    }


    if (
        typeof value.action_id
        !==
        "number"
    ) {

        return null;
    }


    if (
        typeof value.insight_id
        !==
        "number"
    ) {

        return null;
    }


    if (
        typeof value.title
        !==
        "string"
    ) {

        return null;
    }


    if (
        !isActionStatus(
            value.status,
        )
    ) {

        return null;
    }


    const ownerName =
        (
            typeof value.owner_name
            ===
            "string"
            ?
            value.owner_name
            :
            null
        );


    const dueDate =
        (
            typeof value.due_date
            ===
            "string"
            ?
            value.due_date
            :
            null
        );


    const notes =
        (
            typeof value.notes
            ===
            "string"
            ?
            value.notes
            :
            null
        );


    const createdAt =
        (
            typeof value.created_at
            ===
            "string"
            ?
            value.created_at
            :
            ""
        );


    const updatedAt =
        (
            typeof value.updated_at
            ===
            "string"
            ?
            value.updated_at
            :
            createdAt
        );


    const completedAt =
        (
            typeof value.completed_at
            ===
            "string"
            ?
            value.completed_at
            :
            null
        );


    return {
        action_id:
            value.action_id,

        insight_id:
            value.insight_id,

        title:
            value.title,

        owner_name:
            ownerName,

        status:
            value.status,

        due_date:
            dueDate,

        notes:
            notes,

        created_at:
            createdAt,

        updated_at:
            updatedAt,

        completed_at:
            completedAt,
    };
}


// ============================================================
// ACTION LIST PARSER
// ============================================================

function extractActionResults(
    payload:
        unknown,
): InsightAction[] {

    let rawResults:
        unknown =
        null;


    if (
        Array.isArray(
            payload,
        )
    ) {

        rawResults =
            payload;
    }
    else if (
        isRecord(
            payload,
        )
    ) {

        if (
            Array.isArray(
                payload.results,
            )
        ) {

            rawResults =
                payload.results;
        }
        else if (
            isRecord(
                payload.data,
            )
            &&
            Array.isArray(
                payload.data.results,
            )
        ) {

            rawResults =
                payload.data.results;
        }
    }


    if (
        !Array.isArray(
            rawResults,
        )
    ) {

        return [];
    }


    const actions:
        InsightAction[] =
        [];


    for (
        const rawAction
        of
        rawResults
    ) {

        const action =
            parseInsightAction(
                rawAction,
            );


        if (
            action
        ) {

            actions.push(
                action,
            );
        }
    }


    return actions;
}


// ============================================================
// ERROR MESSAGE
// ============================================================

function extractErrorMessage(
    payload:
        unknown,

    fallback:
        string,
): string {

    if (
        typeof payload
        ===
        "string"
        &&
        payload.trim()
    ) {

        return payload.trim();
    }


    if (
        !isRecord(
            payload,
        )
    ) {

        return fallback;
    }


    if (
        typeof payload.detail
        ===
        "string"
        &&
        payload.detail.trim()
    ) {

        return payload.detail.trim();
    }


    if (
        typeof payload.error
        ===
        "string"
        &&
        payload.error.trim()
    ) {

        return payload.error.trim();
    }


    if (
        typeof payload.message
        ===
        "string"
        &&
        payload.message.trim()
    ) {

        return payload.message.trim();
    }


    return fallback;
}


// ============================================================
// LABEL HELPERS
// ============================================================

function statusLabel(
    status:
        ActionStatus,
): string {

    switch (
        status
    ) {

        case "OPEN":

            return "Open";


        case "IN_PROGRESS":

            return "In progress";


        case "BLOCKED":

            return "Blocked";


        case "COMPLETED":

            return "Completed";
    }
}


// ============================================================
// DATE HELPER
// ============================================================

function formatDate(
    value:
        string | null,
): string {

    if (
        !value
    ) {

        return "No due date";
    }


    const date =
        new Date(
            `${value}T00:00:00`,
        );


    if (
        Number.isNaN(
            date.getTime(),
        )
    ) {

        return value;
    }


    return date.toLocaleDateString(
        "en-US",
        {
            month:
                "short",

            day:
                "numeric",

            year:
                "numeric",
        },
    );
}


function formatUpdatedDate(
    value:
        string,
): string {

    if (
        !value
    ) {

        return "Unknown";
    }


    const date =
        new Date(
            value,
        );


    if (
        Number.isNaN(
            date.getTime(),
        )
    ) {

        return "Unknown";
    }


    return date.toLocaleDateString(
        "en-US",
        {
            month:
                "short",

            day:
                "numeric",
        },
    );
}


// ============================================================
// COMPONENT
// ============================================================

export default function ActionPanel(
    {
        insightId,
    }: Props,
) {

    // ========================================================
    // DATA
    // ========================================================

    const [
        actions,
        setActions,
    ] =
        useState<
            InsightAction[]
        >(
            [],
        );


    // ========================================================
    // FORM
    // ========================================================

    const [
        title,
        setTitle,
    ] =
        useState(
            "",
        );


    const [
        owner,
        setOwner,
    ] =
        useState(
            "",
        );


    const [
        dueDate,
        setDueDate,
    ] =
        useState(
            "",
        );


    const [
        notes,
        setNotes,
    ] =
        useState(
            "",
        );


    // ========================================================
    // UI STATE
    // ========================================================

    const [
        loading,
        setLoading,
    ] =
        useState(
            true,
        );


    const [
        saving,
        setSaving,
    ] =
        useState(
            false,
        );


    const [
        updatingActionId,
        setUpdatingActionId,
    ] =
        useState<
            number | null
        >(
            null,
        );


    const [
        deletingActionId,
        setDeletingActionId,
    ] =
        useState<
            number | null
        >(
            null,
        );


    const [
        error,
        setError,
    ] =
        useState<
            string | null
        >(
            null,
        );


    // ========================================================
    // LOAD ACTIONS
    // ========================================================

    const loadActions =
        useCallback(
            async () => {

                try {

                    const response =
                        await fetch(
                            `/api/actions/${insightId}`,
                            {
                                method:
                                    "GET",

                                cache:
                                    "no-store",
                            },
                        );


                    const payload:
                        unknown =
                        await response.json();


                    if (
                        !response.ok
                    ) {

                        throw new Error(
                            extractErrorMessage(
                                payload,
                                "Actions could not be loaded.",
                            ),
                        );
                    }


                    const results =
                        extractActionResults(
                            payload,
                        );


                    setActions(
                        results,
                    );


                    setError(
                        null,
                    );

                }
                catch (
                    loadError
                ) {

                    const message =
                        (
                            loadError
                            instanceof
                            Error
                            ?
                            loadError.message
                            :
                            "Actions could not be loaded."
                        );


                    setError(
                        message,
                    );

                }
                finally {

                    setLoading(
                        false,
                    );
                }

            },
            [
                insightId,
            ],
        );


    // ========================================================
    // INITIAL LOAD
    //
    // We schedule the async call rather than synchronously
    // invoking a state-changing function inside the effect.
    // ========================================================

    useEffect(
        () => {

            const timer =
                window.setTimeout(
                    () => {

                        void loadActions();

                    },
                    0,
                );


            return () => {

                window.clearTimeout(
                    timer,
                );
            };

        },
        [
            loadActions,
        ],
    );


    // ========================================================
    // CREATE ACTION
    // ========================================================

    async function createAction() {

        const cleanTitle =
            title.trim();


        if (
            !cleanTitle
        ) {

            setError(
                "Enter an action title.",
            );

            return;
        }


        setSaving(
            true,
        );


        setError(
            null,
        );


        try {

            const response =
                await fetch(
                    `/api/actions/${insightId}`,
                    {
                        method:
                            "POST",

                        headers: {
                            "Content-Type":
                                "application/json",
                        },

                        body:
                            JSON.stringify(
                                {
                                    title:
                                        cleanTitle,

                                    owner:
                                        (
                                            owner.trim()
                                            ||
                                            null
                                        ),

                                    due_date:
                                        (
                                            dueDate
                                            ||
                                            null
                                        ),

                                    notes:
                                        (
                                            notes.trim()
                                            ||
                                            null
                                        ),
                                },
                            ),
                    },
                );


            const payload:
                unknown =
                await response.json();


            if (
                !response.ok
            ) {

                throw new Error(
                    extractErrorMessage(
                        payload,
                        "Action could not be created.",
                    ),
                );
            }


            setTitle(
                "",
            );


            setOwner(
                "",
            );


            setDueDate(
                "",
            );


            setNotes(
                "",
            );


            await loadActions();

        }
        catch (
            createError
        ) {

            const message =
                (
                    createError
                    instanceof
                    Error
                    ?
                    createError.message
                    :
                    "Action could not be created."
                );


            setError(
                message,
            );

        }
        finally {

            setSaving(
                false,
            );
        }
    }


    // ========================================================
    // UPDATE ACTION STATUS
    // ========================================================

    async function updateStatus(
        actionId:
            number,

        status:
            ActionStatus,
    ) {

        setUpdatingActionId(
            actionId,
        );


        setError(
            null,
        );


        try {

            const response =
                await fetch(
                    `/api/actions/item/${actionId}`,
                    {
                        method:
                            "PATCH",

                        headers: {
                            "Content-Type":
                                "application/json",
                        },

                        body:
                            JSON.stringify(
                                {
                                    status:
                                        status,
                                },
                            ),
                    },
                );


            const payload:
                unknown =
                await response.json();


            if (
                !response.ok
            ) {

                throw new Error(
                    extractErrorMessage(
                        payload,
                        "Action could not be updated.",
                    ),
                );
            }


            await loadActions();

        }
        catch (
            updateError
        ) {

            const message =
                (
                    updateError
                    instanceof
                    Error
                    ?
                    updateError.message
                    :
                    "Action could not be updated."
                );


            setError(
                message,
            );

        }
        finally {

            setUpdatingActionId(
                null,
            );
        }
    }


    // ========================================================
    // DELETE ACTION
    // ========================================================

    async function removeAction(
        actionId:
            number,
    ) {

        const confirmed =
            window.confirm(
                "Delete this management action?",
            );


        if (
            !confirmed
        ) {

            return;
        }


        setDeletingActionId(
            actionId,
        );


        setError(
            null,
        );


        try {

            const response =
                await fetch(
                    `/api/actions/item/${actionId}`,
                    {
                        method:
                            "DELETE",
                    },
                );


            const responseText =
                await response.text();


            let payload:
                unknown =
                null;


            if (
                responseText.trim()
            ) {

                try {

                    payload =
                        JSON.parse(
                            responseText,
                        );

                }
                catch {

                    payload =
                        responseText;
                }
            }


            if (
                !response.ok
            ) {

                throw new Error(
                    extractErrorMessage(
                        payload,
                        "Action could not be deleted.",
                    ),
                );
            }


            await loadActions();

        }
        catch (
            deleteError
        ) {

            const message =
                (
                    deleteError
                    instanceof
                    Error
                    ?
                    deleteError.message
                    :
                    "Action could not be deleted."
                );


            setError(
                message,
            );

        }
        finally {

            setDeletingActionId(
                null,
            );
        }
    }


    // ========================================================
    // RENDER
    // ========================================================

    return (

        <section
            className=
                "action-panel"
        >

            {/* =================================================
                HEADER
            ================================================= */}

            <div
                className=
                    "action-panel-header"
            >

                <div>

                    <span
                        className=
                            "section-kicker"
                    >

                        ACTION TRACKER

                    </span>


                    <h2>

                        Move insight to action

                    </h2>


                    <p>

                        Convert the diagnosis into a management
                        action, assign ownership and track its
                        progress through completion.

                    </p>

                </div>


                <div
                    className=
                        "action-count"
                >

                    <strong>

                        {
                            actions.length
                        }

                    </strong>


                    <span>

                        {
                            actions.length
                            ===
                            1
                            ?
                            "action"
                            :
                            "actions"
                        }

                    </span>

                </div>

            </div>


            {/* =================================================
                CREATE ACTION FORM
            ================================================= */}

            <div
                className=
                    "action-create-card"
            >

                <div
                    className=
                        "action-form-grid"
                >

                    <label
                        className=
                            "action-field action-field-wide"
                    >

                        <span>

                            Action title

                        </span>


                        <input
                            type=
                                "text"

                            value={
                                title
                            }

                            placeholder=
                                "e.g. Review South discount depth"

                            onChange={
                                (
                                    event,
                                ) => {

                                    setTitle(
                                        event.currentTarget.value,
                                    );

                                }
                            }
                        />

                    </label>


                    <label
                        className=
                            "action-field"
                    >

                        <span>

                            Owner

                        </span>


                        <input
                            type=
                                "text"

                            value={
                                owner
                            }

                            placeholder=
                                "e.g. Commercial Manager"

                            onChange={
                                (
                                    event,
                                ) => {

                                    setOwner(
                                        event.currentTarget.value,
                                    );

                                }
                            }
                        />

                    </label>


                    <label
                        className=
                            "action-field"
                    >

                        <span>

                            Due date

                        </span>


                        <input
                            type=
                                "date"

                            value={
                                dueDate
                            }

                            onChange={
                                (
                                    event,
                                ) => {

                                    setDueDate(
                                        event.currentTarget.value,
                                    );

                                }
                            }
                        />

                    </label>


                    <label
                        className=
                            "action-field action-field-wide"
                    >

                        <span>

                            Notes

                        </span>


                        <textarea
                            rows={
                                3
                            }

                            value={
                                notes
                            }

                            placeholder=
                                "Add context, expected outcome or follow-up notes."

                            onChange={
                                (
                                    event,
                                ) => {

                                    setNotes(
                                        event.currentTarget.value,
                                    );

                                }
                            }
                        />

                    </label>

                </div>


                <button
                    type=
                        "button"

                    className=
                        "action-create-button"

                    disabled={
                        saving
                        ||
                        !title.trim()
                    }

                    onClick={
                        () => {

                            void createAction();

                        }
                    }
                >

                    {
                        saving
                        ?
                        "Adding action..."
                        :
                        "Add management action"
                    }

                </button>

            </div>


            {/* =================================================
                ERROR MESSAGE
            ================================================= */}

            {
                error
                &&
                (

                    <div
                        className=
                            "action-error"
                    >

                        {
                            error
                        }

                    </div>

                )
            }


            {/* =================================================
                LOADING STATE
            ================================================= */}

            {
                loading
                &&
                (

                    <div
                        className=
                            "action-empty"
                    >

                        Loading actions...

                    </div>

                )
            }


            {/* =================================================
                EMPTY STATE
            ================================================= */}

            {
                !loading
                &&
                actions.length
                ===
                0
                &&
                (

                    <div
                        className=
                            "action-empty"
                    >

                        <strong>

                            No management actions yet.

                        </strong>


                        <span>

                            Add the first action above to begin
                            tracking execution against this
                            business insight.

                        </span>

                    </div>

                )
            }


            {/* =================================================
                ACTION LIST
            ================================================= */}

            {
                actions.length
                >
                0
                &&
                (

                    <div
                        className=
                            "action-list"
                    >

                        {
                            actions.map(
                                (
                                    action,
                                ) => (

                                    <article
                                        className=
                                            "action-item"

                                        key={
                                            action.action_id
                                        }
                                    >

                                        <div
                                            className=
                                                "action-item-main"
                                        >

                                            <div
                                                className=
                                                    "action-title-row"
                                            >

                                                <div>

                                                    <span
                                                        className={
                                                            (
                                                                "action-status-pill "
                                                                +
                                                                `action-status-${action.status.toLowerCase()}`
                                                            )
                                                        }
                                                    >

                                                        {
                                                            statusLabel(
                                                                action.status,
                                                            )
                                                        }

                                                    </span>


                                                    <h3>

                                                        {
                                                            action.title
                                                        }

                                                    </h3>

                                                </div>


                                                <button
                                                    type=
                                                        "button"

                                                    className=
                                                        "action-delete-button"

                                                    disabled={
                                                        deletingActionId
                                                        ===
                                                        action.action_id
                                                    }

                                                    onClick={
                                                        () => {

                                                            void removeAction(
                                                                action.action_id,
                                                            );

                                                        }
                                                    }
                                                >

                                                    {
                                                        deletingActionId
                                                        ===
                                                        action.action_id
                                                        ?
                                                        "Deleting..."
                                                        :
                                                        "Delete"
                                                    }

                                                </button>

                                            </div>


                                            <div
                                                className=
                                                    "action-meta"
                                            >

                                                <span>

                                                    <strong>

                                                        Owner

                                                    </strong>


                                                    {
                                                        action.owner_name
                                                        ??
                                                        "Unassigned"
                                                    }

                                                </span>


                                                <span>

                                                    <strong>

                                                        Due

                                                    </strong>


                                                    {
                                                        formatDate(
                                                            action.due_date,
                                                        )
                                                    }

                                                </span>


                                                <span>

                                                    <strong>

                                                        Updated

                                                    </strong>


                                                    {
                                                        formatUpdatedDate(
                                                            action.updated_at,
                                                        )
                                                    }

                                                </span>

                                            </div>


                                            {
                                                action.notes
                                                &&
                                                (

                                                    <p
                                                        className=
                                                            "action-notes"
                                                    >

                                                        {
                                                            action.notes
                                                        }

                                                    </p>

                                                )
                                            }

                                        </div>


                                        <div
                                            className=
                                                "action-status-control"
                                        >

                                            <label>

                                                <span>

                                                    Status

                                                </span>


                                                <select
                                                    value={
                                                        action.status
                                                    }

                                                    disabled={
                                                        updatingActionId
                                                        ===
                                                        action.action_id
                                                    }

                                                    onChange={
                                                        (
                                                            event,
                                                        ) => {

                                                            const nextStatus =
                                                                parseActionStatus(
                                                                    event.currentTarget.value,
                                                                );


                                                            if (
                                                                nextStatus
                                                            ) {

                                                                void updateStatus(
                                                                    action.action_id,
                                                                    nextStatus,
                                                                );
                                                            }

                                                        }
                                                    }
                                                >

                                                    <option
                                                        value=
                                                            "OPEN"
                                                    >

                                                        Open

                                                    </option>


                                                    <option
                                                        value=
                                                            "IN_PROGRESS"
                                                    >

                                                        In progress

                                                    </option>


                                                    <option
                                                        value=
                                                            "BLOCKED"
                                                    >

                                                        Blocked

                                                    </option>


                                                    <option
                                                        value=
                                                            "COMPLETED"
                                                    >

                                                        Completed

                                                    </option>

                                                </select>

                                            </label>

                                        </div>

                                    </article>

                                ),
                            )
                        }

                    </div>

                )
            }

        </section>
    );
}