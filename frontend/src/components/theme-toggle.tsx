"use client";

import {
    useEffect,
    useRef,
} from "react";


// ============================================================
// TYPES
// ============================================================

type ThemeMode =
    "system"
    |
    "light"
    |
    "dark";


const STORAGE_KEY =
    "aibi-theme";


// ============================================================
// TYPE GUARD
// ============================================================

function isThemeMode(
    value: string | null,
): value is ThemeMode {

    return (
        value
        ===
        "system"

        ||
        value
        ===
        "light"

        ||
        value
        ===
        "dark"
    );
}


// ============================================================
// STORED THEME
// ============================================================

function getStoredTheme():
ThemeMode {

    if (
        typeof window
        ===
        "undefined"
    ) {

        return "system";
    }


    const stored =
        window
            .localStorage
            .getItem(
                STORAGE_KEY,
            );


    if (
        isThemeMode(
            stored,
        )
    ) {

        return stored;
    }


    return "system";
}


// ============================================================
// RESOLVE SYSTEM THEME
// ============================================================

function resolveTheme(
    mode: ThemeMode,
):
"light" | "dark" {

    if (
        mode
        ===
        "light"
    ) {

        return "light";
    }


    if (
        mode
        ===
        "dark"
    ) {

        return "dark";
    }


    if (
        typeof window
        ===
        "undefined"
    ) {

        return "light";
    }


    const prefersDark =
        window
            .matchMedia(
                "(prefers-color-scheme: dark)",
            )
            .matches;


    return (
        prefersDark
            ?
            "dark"
            :
            "light"
    );
}


// ============================================================
// APPLY THEME
// ============================================================

function applyTheme(
    mode: ThemeMode,
): void {

    if (
        typeof document
        ===
        "undefined"
    ) {

        return;
    }


    const resolvedTheme =
        resolveTheme(
            mode,
        );


    document
        .documentElement
        .setAttribute(
            "data-theme",
            resolvedTheme,
        );


    document
        .documentElement
        .setAttribute(
            "data-theme-mode",
            mode,
        );
}


// ============================================================
// THEME TOGGLE
// ============================================================

export default function ThemeToggle() {

    const selectRef =
        useRef<
            HTMLSelectElement
        >(
            null,
        );


    // ========================================================
    // INITIALIZE + LISTEN FOR SYSTEM THEME CHANGES
    // ========================================================

    useEffect(
        () => {

            const storedTheme =
                getStoredTheme();


            if (
                selectRef.current
            ) {

                selectRef
                    .current
                    .value =
                        storedTheme;
            }


            applyTheme(
                storedTheme,
            );


            const mediaQuery =
                window.matchMedia(
                    "(prefers-color-scheme: dark)",
                );


            const handleSystemThemeChange =
                () => {

                    const currentMode =
                        getStoredTheme();


                    if (
                        currentMode
                        ===
                        "system"
                    ) {

                        applyTheme(
                            "system",
                        );
                    }
                };


            mediaQuery.addEventListener(
                "change",
                handleSystemThemeChange,
            );


            return () => {

                mediaQuery.removeEventListener(
                    "change",
                    handleSystemThemeChange,
                );
            };

        },
        [],
    );


    // ========================================================
    // CHANGE THEME
    // ========================================================

    function handleThemeChange(
        event:
            React.ChangeEvent<HTMLSelectElement>,
    ): void {

        const selectedValue =
            event
                .target
                .value;


        if (
            !isThemeMode(
                selectedValue,
            )
        ) {

            return;
        }


        window
            .localStorage
            .setItem(
                STORAGE_KEY,
                selectedValue,
            );


        applyTheme(
            selectedValue,
        );
    }


    // ========================================================
    // UI
    // ========================================================

    return (

        <label className="theme-picker">

            <span>
                Theme
            </span>


            <select
                ref={
                    selectRef
                }
                aria-label="Dashboard theme"
                defaultValue="system"
                onChange={
                    handleThemeChange
                }
            >

                <option value="system">
                    System
                </option>


                <option value="light">
                    Light
                </option>


                <option value="dark">
                    Dark
                </option>

            </select>

        </label>
    );
}