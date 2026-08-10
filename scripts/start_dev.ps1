$ErrorActionPreference = "Stop"

# ============================================================
# PROJECT ROOT
# ============================================================

$ProjectRoot = (
    Resolve-Path (
        Join-Path $PSScriptRoot ".."
    )
).Path

$VenvActivate = Join-Path `
    $ProjectRoot `
    ".venv\Scripts\Activate.ps1"


# ============================================================
# HELPERS
# ============================================================

function Test-LocalPort {
    param(
        [Parameter(Mandatory = $true)]
        [int]$Port
    )

    try {
        $client = New-Object System.Net.Sockets.TcpClient

        $result = $client.BeginConnect(
            "127.0.0.1",
            $Port,
            $null,
            $null
        )

        $connected = $result.AsyncWaitHandle.WaitOne(
            500
        )

        if (-not $connected) {
            $client.Close()
            return $false
        }

        $client.EndConnect(
            $result
        )

        $client.Close()

        return $true
    }
    catch {
        return $false
    }
}


function Wait-ForPort {
    param(
        [Parameter(Mandatory = $true)]
        [int]$Port,

        [Parameter(Mandatory = $true)]
        [string]$ServiceName,

        [int]$TimeoutSeconds = 30
    )

    Write-Host ""
    Write-Host "Waiting for $ServiceName on port $Port..."

    $deadline = (
        Get-Date
    ).AddSeconds(
        $TimeoutSeconds
    )

    while (
        (Get-Date) -lt $deadline
    ) {

        if (
            Test-LocalPort `
                -Port $Port
        ) {

            Write-Host "$ServiceName is reachable."
            return $true
        }

        Start-Sleep -Seconds 1
    }

    Write-Host ""
    Write-Host "ERROR: $ServiceName did not start within $TimeoutSeconds seconds."
    return $false
}


# ============================================================
# HEADER
# ============================================================

Write-Host ""
Write-Host "============================================"
Write-Host "AI BUSINESS INTELLIGENCE ANALYST"
Write-Host "Starting local development services"
Write-Host "============================================"
Write-Host ""

Write-Host "Project root:"
Write-Host $ProjectRoot
Write-Host ""


# ============================================================
# VALIDATE PYTHON ENVIRONMENT
# ============================================================

if (
    -not (
        Test-Path $VenvActivate
    )
) {
    throw "Python virtual environment was not found at: $VenvActivate"
}


# ============================================================
# VALIDATE N8N
# ============================================================

$n8nCommand = (
    Get-Command n8n `
        -ErrorAction SilentlyContinue
)

if (
    -not $n8nCommand
) {
    throw "n8n command was not found in PATH. Run 'n8n --version' manually first."
}

$n8nPath = $n8nCommand.Source

Write-Host "n8n executable:"
Write-Host $n8nPath
Write-Host ""


# ============================================================
# START FASTAPI
# ============================================================

if (
    Test-LocalPort `
        -Port 8000
) {

    Write-Host "FastAPI is already running on port 8000."
}
else {

    $FastApiCommand = @"
Set-Location -LiteralPath '$ProjectRoot'
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
& '$VenvActivate'
`$Host.UI.RawUI.WindowTitle = 'AI BI - FastAPI'
python -m uvicorn backend.app.main:app --reload
"@

    Start-Process `
        powershell.exe `
        -ArgumentList @(
            "-NoExit",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            $FastApiCommand
        )
}


$fastApiReady = (
    Wait-ForPort `
        -Port 8000 `
        -ServiceName "FastAPI" `
        -TimeoutSeconds 30
)

if (
    -not $fastApiReady
) {
    throw "FastAPI failed to start."
}


# ============================================================
# VERIFY FASTAPI HEALTH
# ============================================================

try {

    $health = Invoke-RestMethod `
        -Method Get `
        -Uri "http://127.0.0.1:8000/health" `
        -TimeoutSec 10

    Write-Host ""
    Write-Host "FastAPI health check passed."
}
catch {

    throw "FastAPI port opened, but /health did not respond correctly."
}


# ============================================================
# START N8N
# ============================================================

if (
    Test-LocalPort `
        -Port 5678
) {

    Write-Host ""
    Write-Host "n8n is already running on port 5678."
}
else {

    $N8nCommand = @"
Set-Location -LiteralPath '$ProjectRoot'
`$Host.UI.RawUI.WindowTitle = 'AI BI - n8n'
`$env:GENERIC_TIMEZONE = 'Asia/Karachi'
`$env:TZ = 'Asia/Karachi'
& '$n8nPath' start
"@

    Start-Process `
        powershell.exe `
        -ArgumentList @(
            "-NoExit",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            $N8nCommand
        )
}


$n8nReady = (
    Wait-ForPort `
        -Port 5678 `
        -ServiceName "n8n" `
        -TimeoutSeconds 45
)

if (
    -not $n8nReady
) {
    throw "n8n failed to start. Check the 'AI BI - n8n' PowerShell window for the actual startup error."
}


# ============================================================
# COMPLETE
# ============================================================

Write-Host ""
Write-Host "============================================"
Write-Host "DEVELOPMENT SERVICES READY"
Write-Host "============================================"
Write-Host ""
Write-Host "FastAPI:"
Write-Host "http://127.0.0.1:8000"
Write-Host ""
Write-Host "n8n:"
Write-Host "http://127.0.0.1:5678"
Write-Host ""
Write-Host "FastAPI health: OK"
Write-Host "n8n port:       OK"
Write-Host ""