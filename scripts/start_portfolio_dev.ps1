param
(
    [switch]$NoBrowser
)


# ============================================================
# POWERSHELL CONFIGURATION
# ============================================================

Set-StrictMode -Version Latest

$ErrorActionPreference = "Stop"


# ============================================================
# PROJECT PATHS
# ============================================================

$ProjectRoot = Split-Path -Parent $PSScriptRoot

$FrontendRoot = Join-Path $ProjectRoot "frontend"

$PythonExe = Join-Path $ProjectRoot ".venv\Scripts\python.exe"


# ============================================================
# PORTS
# ============================================================

$OllamaPort = 11434

$FastApiPort = 8000

$NextPort = 3000


# ============================================================
# URLS
# ============================================================

$FrontendUrl = "http://localhost:3000"

$FastApiUrl = "http://127.0.0.1:8000"

$OllamaUrl = "http://127.0.0.1:11434"


# ============================================================
# DISPLAY HELPERS
# ============================================================

function Write-Step
{
    param
    (
        [Parameter(Mandatory = $true)]
        [string]$Message
    )


    Write-Host ""

    Write-Host "============================================================"

    Write-Host $Message -ForegroundColor Cyan

    Write-Host "============================================================"
}


function Write-Success
{
    param
    (
        [Parameter(Mandatory = $true)]
        [string]$Message
    )


    Write-Host $Message -ForegroundColor Green
}


function Write-Info
{
    param
    (
        [Parameter(Mandatory = $true)]
        [string]$Message
    )


    Write-Host $Message -ForegroundColor Gray
}


# ============================================================
# TEST LOCAL PORT
# ============================================================

function Test-LocalPort
{
    param
    (
        [Parameter(Mandatory = $true)]
        [int]$Port
    )


    try
    {
        $client = New-Object System.Net.Sockets.TcpClient


        try
        {
            $result = $client.BeginConnect(
                "127.0.0.1",
                $Port,
                $null,
                $null
            )


            $connected = $result.AsyncWaitHandle.WaitOne(
                600,
                $false
            )


            if (-not $connected)
            {
                return $false
            }


            $client.EndConnect(
                $result
            )


            return $true
        }
        finally
        {
            $client.Close()
        }
    }
    catch
    {
        return $false
    }
}


# ============================================================
# WAIT FOR PORT
# ============================================================

function Wait-ForPort
{
    param
    (
        [Parameter(Mandatory = $true)]
        [int]$Port,

        [Parameter(Mandatory = $true)]
        [string]$ServiceName,

        [int]$TimeoutSeconds = 40
    )


    $startedAt = Get-Date


    while ($true)
    {
        if (Test-LocalPort -Port $Port)
        {
            Write-Success "$ServiceName is ready on port $Port."

            return
        }


        $elapsed = (Get-Date) - $startedAt


        if ($elapsed.TotalSeconds -ge $TimeoutSeconds)
        {
            $message = "{0} did not become ready on port {1} within {2} seconds." -f `
                $ServiceName, `
                $Port, `
                $TimeoutSeconds


            throw $message
        }


        Start-Sleep -Milliseconds 750
    }
}


# ============================================================
# CHECK REQUIRED FILES
# ============================================================

Write-Step "AI BI ANALYST - LOCAL DEVELOPMENT STARTUP"


Set-Location $ProjectRoot


if (-not (Test-Path $PythonExe))
{
    throw "Virtual environment Python was not found at: $PythonExe"
}


if (-not (Test-Path $FrontendRoot))
{
    throw "Frontend directory was not found at: $FrontendRoot"
}


$npmCommand = Get-Command npm -ErrorAction SilentlyContinue


if ($null -eq $npmCommand)
{
    throw "npm is not available in PATH."
}


Write-Info "Project root: $ProjectRoot"

Write-Info "Python: $PythonExe"

Write-Info "Frontend: $FrontendRoot"


# ============================================================
# CHECK OLLAMA
# ============================================================

Write-Step "CHECKING OLLAMA"


$ollamaCandidates = @(
    (Join-Path $env:LOCALAPPDATA "Programs\Ollama\ollama.exe"),
    (Join-Path $env:LOCALAPPDATA "Ollama\ollama.exe")
)


if ($env:ProgramFiles)
{
    $ollamaCandidates += (
        Join-Path $env:ProgramFiles "Ollama\ollama.exe"
    )
}


$ollamaExe = $null


foreach ($candidate in $ollamaCandidates)
{
    if (Test-Path $candidate)
    {
        $ollamaExe = $candidate

        break
    }
}


if (Test-LocalPort -Port $OllamaPort)
{
    Write-Success "Ollama is already running."
}
elseif ($null -ne $ollamaExe)
{
    Write-Info "Starting Ollama..."


    Start-Process `
        -FilePath $ollamaExe `
        -ArgumentList "serve" `
        -WindowStyle Hidden


    Wait-ForPort `
        -Port $OllamaPort `
        -ServiceName "Ollama" `
        -TimeoutSeconds 30
}
else
{
    Write-Warning "Ollama executable was not found."

    Write-Warning "Deterministic analyst paths will still work."

    Write-Warning "Local-AI fallback will be unavailable."
}


# ============================================================
# CHECK FASTAPI
# ============================================================

Write-Step "CHECKING FASTAPI"


if (Test-LocalPort -Port $FastApiPort)
{
    Write-Success "FastAPI is already running."
}
else
{
    Write-Info "Starting FastAPI with automatic reload..."


    $backendCommand = @"
Set-Location '$ProjectRoot'
& '$PythonExe' -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
"@


    Start-Process `
        -FilePath "powershell.exe" `
        -ArgumentList @(
            "-NoExit",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            $backendCommand
        )


    Wait-ForPort `
        -Port $FastApiPort `
        -ServiceName "FastAPI" `
        -TimeoutSeconds 45
}


# ============================================================
# CHECK NEXT.JS
# ============================================================

Write-Step "CHECKING NEXT.JS"


if (Test-LocalPort -Port $NextPort)
{
    Write-Success "Next.js is already running."
}
else
{
    Write-Info "Starting Next.js development server..."


    $frontendCommand = @"
Set-Location '$FrontendRoot'
npm run dev
"@


    Start-Process `
        -FilePath "powershell.exe" `
        -ArgumentList @(
            "-NoExit",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            $frontendCommand
        )


    Wait-ForPort `
        -Port $NextPort `
        -ServiceName "Next.js" `
        -TimeoutSeconds 60
}


# ============================================================
# OPEN BROWSER
# ============================================================

if (-not $NoBrowser)
{
    Write-Step "OPENING PORTFOLIO"


    Start-Process $FrontendUrl
}


# ============================================================
# FINAL STATUS
# ============================================================

Write-Step "LOCAL DEVELOPMENT ENVIRONMENT READY"


Write-Success "Frontend: $FrontendUrl"

Write-Success "FastAPI: $FastApiUrl"

Write-Success "Ollama: $OllamaUrl"


Write-Host ""

Write-Host "Automatic development behavior:" -ForegroundColor White

Write-Host "  Frontend file save -> Next.js HMR" -ForegroundColor Gray

Write-Host "  Backend Python save -> Uvicorn reload" -ForegroundColor Gray

Write-Host "  Backend restart -> browser recovery reload" -ForegroundColor Gray


Write-Host ""

Write-Host "Development servers run in separate PowerShell windows." -ForegroundColor Gray