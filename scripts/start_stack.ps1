param(
    [string]$AntiApiDir = "",
    [int]$AntiApiPort = 8964,
    [int]$AppPort = 8000,
    [switch]$SkipIngest
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
if (-not $AntiApiDir) {
    $AntiApiDir = Join-Path (Split-Path -Parent $projectRoot) "anti-api-main"
}

if (-not (Test-Path $AntiApiDir)) {
    throw "Anti-API directory not found: $AntiApiDir"
}

$venvPython = Join-Path $projectRoot ".venv\Scripts\python.exe"
$pythonExe = if (Test-Path $venvPython) { $venvPython } else { "python" }

function Wait-HttpReady {
    param(
        [Parameter(Mandatory = $true)][string]$Url,
        [int]$TimeoutSeconds = 120
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    do {
        try {
            Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 5 | Out-Null
            return $true
        } catch {
            Start-Sleep -Seconds 2
        }
    } while ((Get-Date) -lt $deadline)

    return $false
}

Write-Host "Starting Anti-API from $AntiApiDir"
Start-Process -FilePath "bun" -ArgumentList @("run", "src/main.ts", "start") -WorkingDirectory $AntiApiDir

if (-not (Wait-HttpReady -Url "http://localhost:$AntiApiPort/health" -TimeoutSeconds 180)) {
    throw "Anti-API did not become ready on http://localhost:$AntiApiPort/health"
}

Write-Host "Bootstrapping Anti-API routing for gpt-5.4 and claude-opus-4-6"
& $pythonExe "scripts/bootstrap_antiapi_routing.py" "--anti-api-url" "http://localhost:$AntiApiPort"
if ($LASTEXITCODE -ne 0) {
    throw "Anti-API routing bootstrap failed."
}

if (-not $SkipIngest) {
    Write-Host "Running document ingestion"
    & $pythonExe "scripts/ingest.py"
    if ($LASTEXITCODE -ne 0) {
        throw "Document ingestion failed."
    }
}

Write-Host "Starting FastAPI app on port $AppPort"
& $pythonExe -m uvicorn app.main:app --host 0.0.0.0 --port $AppPort --reload
