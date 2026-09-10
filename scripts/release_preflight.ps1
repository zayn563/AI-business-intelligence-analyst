param(
    [switch]$SkipGitCleanCheck
)

$ErrorActionPreference = "Stop"

Set-StrictMode `
    -Version Latest


function Write-Section {

    param(
        [Parameter(Mandatory = $true)]
        [string]$Title
    )

    Write-Host ""
    Write-Host (
        "=" * 72
    ) -ForegroundColor DarkGray

    Write-Host $Title `
        -ForegroundColor Cyan

    Write-Host (
        "=" * 72
    ) -ForegroundColor DarkGray
}


function Stop-Release {

    param(
        [Parameter(Mandatory = $true)]
        [string]$Message
    )

    Write-Host ""
    Write-Host "RELEASE PREFLIGHT FAILED" `
        -ForegroundColor Red

    Write-Host $Message `
        -ForegroundColor Red

    exit 1
}


$ProjectRoot =
    Split-Path `
        -Parent `
        $PSScriptRoot


Set-Location `
    $ProjectRoot


Write-Section `
    "AI BI PORTFOLIO RELEASE PREFLIGHT"


Write-Host "Project root:"
Write-Host "  $ProjectRoot"


# ============================================================
# PYTHON ENVIRONMENT
# ============================================================


Write-Section `
    "CHECKING PYTHON ENVIRONMENT"


$PythonExecutable =
    (
        python -c "import sys; print(sys.executable)"
    ).Trim()


Write-Host "Python:"
Write-Host "  $PythonExecutable"


if (
    $PythonExecutable `
        -notmatch `
        "\.venv"
) {

    Stop-Release `
        (
            "The project virtual environment is not active. " +
            "Activate .venv before running the release gate."
        )
}


# ============================================================
# SECRET SAFETY
# ============================================================


Write-Section `
    "CHECKING TRACKED SECRETS"


$TrackedFiles =
    @(
        git ls-files
    )


$ForbiddenTrackedFiles =
    @(
        ".env",
        "frontend/.env.local",
        "secrets/google-service-account.json",
        "google-service-account.json"
    )


foreach (
    $ForbiddenFile
    in
    $ForbiddenTrackedFiles
) {

    if (
        $TrackedFiles `
            -contains `
            $ForbiddenFile
    ) {

        Stop-Release `
            (
                "Sensitive file is tracked by Git: " +
                $ForbiddenFile
            )
    }
}


$SuspiciousTrackedFiles =
    $TrackedFiles |
    Where-Object {

        $_ `
            -match `
            "(?i)(service-account.*\.json|credentials.*\.json|private.*key)"
    }


if (
    $SuspiciousTrackedFiles.Count `
        -gt `
        0
) {

    Write-Host "Potential secret files require manual review:" `
        -ForegroundColor Yellow

    $SuspiciousTrackedFiles |
        ForEach-Object {
            Write-Host "  $_" `
                -ForegroundColor Yellow
        }

    Stop-Release `
        "Review the suspicious tracked files before release."
}


Write-Host "Tracked-secret check passed." `
    -ForegroundColor Green


# ============================================================
# PYTHON COMPILATION
# ============================================================


Write-Section `
    "COMPILING BACKEND"


python -m compileall `
    .\backend `
    .\tests `
    .\scripts


if (
    $LASTEXITCODE `
        -ne `
        0
) {

    Stop-Release `
        "Python compilation failed."
}


Write-Host "Python compilation passed." `
    -ForegroundColor Green


# ============================================================
# BACKEND TESTS
# ============================================================


Write-Section `
    "RUNNING FULL BACKEND TEST SUITE"


python -m pytest -q


if (
    $LASTEXITCODE `
        -ne `
        0
) {

    Stop-Release `
        "Backend tests are not fully green."
}


Write-Host "Backend tests passed." `
    -ForegroundColor Green


# ============================================================
# DATA FRESHNESS
# ============================================================


Write-Section `
    "CHECKING ANALYTICAL DATA FRESHNESS"


python `
    .\scripts\audit_data_freshness.py `
    --require-current


$FreshnessExitCode =
    $LASTEXITCODE


if (
    $FreshnessExitCode `
        -eq `
        2
) {

    Stop-Release `
        (
            "One or more required analytical datasets are stale. " +
            "Update Inventory / Targets before publishing."
        )
}


if (
    $FreshnessExitCode `
        -ne `
        0
) {

    Stop-Release `
        "The data freshness audit failed."
}


Write-Host "All required analytical domains are current." `
    -ForegroundColor Green


# ============================================================
# FRONTEND
# ============================================================


Write-Section `
    "VALIDATING FRONTEND"


Push-Location `
    .\frontend


try {

    npm run lint

    if (
        $LASTEXITCODE `
            -ne `
            0
    ) {

        Stop-Release `
            "Frontend lint failed."
    }


    npm run build

    if (
        $LASTEXITCODE `
            -ne `
            0
    ) {

        Stop-Release `
            "Frontend production build failed."
    }

}
finally {

    Pop-Location
}


Write-Host "Frontend validation passed." `
    -ForegroundColor Green


# ============================================================
# GIT STATE
# ============================================================


if (
    -not
    $SkipGitCleanCheck
) {

    Write-Section `
        "CHECKING GIT WORKING TREE"


    $GitChanges =
        @(
            git status --porcelain
        )


    if (
        $GitChanges.Count `
            -gt `
            0
    ) {

        Write-Host "Uncommitted files:" `
            -ForegroundColor Yellow

        git status --short

        Stop-Release `
            (
                "Commit the intended release files before " +
                "running the final deployment."
            )
    }


    Write-Host "Git working tree is clean." `
        -ForegroundColor Green
}


# ============================================================
# COMPLETE
# ============================================================


Write-Section `
    "RELEASE PREFLIGHT PASSED"


Write-Host ""
Write-Host (
    "The application is ready for the deployment smoke-test stage."
) -ForegroundColor Green

Write-Host ""