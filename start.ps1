param(
    [switch]$BackendOnly,
    [switch]$Restart
)

$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot

$pythonPath = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'

if (-not (Test-Path -LiteralPath $pythonPath)) {
    throw 'Create .venv and install backend dependencies first. Read docs/SETUP.md.'
}

if (-not (Test-Path -LiteralPath 'backend/.env')) {
    Copy-Item 'backend/.env.example' 'backend/.env'
}

if (-not (Test-Path -LiteralPath 'frontend/.env.local')) {
    Copy-Item 'frontend/.env.example' 'frontend/.env.local'
}

# The portable PostgreSQL instance belongs only to this local workspace.
$pgctlPath = Join-Path $PSScriptRoot '.local\postgres\pgsql\bin\pg_ctl.exe'
$pgdataPath = Join-Path $PSScriptRoot '.local\pgdata'

if ((Test-Path -LiteralPath $pgctlPath) -and (Test-Path -LiteralPath $pgdataPath)) {
    & $pgctlPath -D $pgdataPath status *> $null

    if ($LASTEXITCODE -ne 0) {
        $postgresLogPath = Join-Path $PSScriptRoot '.local\postgres.log'
        $postgresArguments = @(
            '-D', $pgdataPath,
            '-l', $postgresLogPath,
            '-o', '-h 127.0.0.1 -p 55432',
            'start'
        )

        & $pgctlPath @postgresArguments

        if ($LASTEXITCODE -ne 0) {
            throw 'Could not start local PostgreSQL. Read .local/postgres.log.'
        }
    }
}

Push-Location backend

try {
    & $pythonPath -m alembic upgrade head

    if ($LASTEXITCODE -ne 0) {
        throw 'Migration failed. Start PostgreSQL and verify backend/.env.'
    }
}
finally {
    Pop-Location
}

New-Item -ItemType Directory -Path '.local' -Force | Out-Null
$backendPidPath = Join-Path $PSScriptRoot '.local\backend.pid'

if ($Restart -and (Test-Path -LiteralPath $backendPidPath)) {
    $ownedProcessId = [int](Get-Content -LiteralPath $backendPidPath)
    $ownedProcess = Get-Process -Id $ownedProcessId -ErrorAction SilentlyContinue

    if ($ownedProcess -and $ownedProcess.Path -eq $pythonPath) {
        Stop-Process -Id $ownedProcessId
    }
}

$apiRunning = $false

try {
    $health = Invoke-RestMethod 'http://127.0.0.1:8000/api/v1/health' -TimeoutSec 2
    $apiRunning = $health.version -eq '1.0.0'
}
catch {}

if (-not $apiRunning) {
    $backendOptions = @{
        PassThru = $true
        FilePath = $pythonPath
        ArgumentList = @(
            '-m', 'uvicorn', 'app.main:app',
            '--host', '127.0.0.1',
            '--port', '8000'
        )
        WorkingDirectory = Join-Path $PSScriptRoot 'backend'
        WindowStyle = 'Hidden'
        RedirectStandardOutput = Join-Path $PSScriptRoot '.local\backend.log'
        RedirectStandardError = Join-Path $PSScriptRoot '.local\backend-error.log'
    }

    $backendProcess = Start-Process @backendOptions
    $backendProcess.Id | Set-Content -LiteralPath $backendPidPath
}

if (-not $BackendOnly) {
    if (-not (Test-Path -LiteralPath 'frontend/node_modules')) {
        throw 'Run npm.cmd install --prefix frontend first.'
    }

    $frontendRunning = $false

    try {
        $response = Invoke-WebRequest 'http://127.0.0.1:3000' -TimeoutSec 2
        $frontendRunning = $response.StatusCode -eq 200
    }
    catch {}

    if (-not $frontendRunning) {
        $npmPath = (Get-Command npm.cmd).Source
        $frontendOptions = @{
            FilePath = $npmPath
            ArgumentList = @('run', 'dev')
            WorkingDirectory = Join-Path $PSScriptRoot 'frontend'
            WindowStyle = 'Hidden'
            RedirectStandardOutput = Join-Path $PSScriptRoot '.local\frontend.log'
            RedirectStandardError = Join-Path $PSScriptRoot '.local\frontend-error.log'
        }

        Start-Process @frontendOptions
    }
}

Write-Host 'CareerPilot is starting. Open http://localhost:3000 after the frontend is ready.'
Write-Host 'API health: http://localhost:8000/api/v1/health'
Write-Host 'Logs: .local/backend.log, .local/backend-error.log, .local/frontend.log'
