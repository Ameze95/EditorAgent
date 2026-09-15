[CmdletBinding()]
param(
    [switch]$InstallSystemDependencies,
    [switch]$SkipFrontend
)

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$backendRoot = Join-Path $repoRoot 'backend'
$frontendRoot = Join-Path $repoRoot 'frontend'
$venvRoot = Join-Path $backendRoot '.venv'
$venvPython = Join-Path $venvRoot 'Scripts\python.exe'

function Require-Command([string]$Name, [string]$InstallHint) {
    if ($null -eq (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "No se encuentra '$Name'. $InstallHint"
    }
}

Write-Host 'EditorAgent setup' -ForegroundColor Cyan
Write-Host "Repositorio: $repoRoot"

if ($null -eq (Get-Command py -ErrorAction SilentlyContinue)) {
    if (-not $InstallSystemDependencies) {
        throw "No se encuentra el launcher 'py'. Ejecuta init.ps1 -InstallSystemDependencies para instalar Python 3.12 mediante winget."
    }
    Require-Command 'winget' 'Instala App Installer de Microsoft.'
    winget install --id Python.Python.3.12 -e --source winget --accept-source-agreements --accept-package-agreements
}

$python312 = & py -3.12 -c "import sys; print(sys.executable)" 2>$null
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($python312)) {
    if (-not $InstallSystemDependencies) {
        throw "Python 3.12 no está instalado. Ejecuta init.ps1 -InstallSystemDependencies."
    }
    winget install --id Python.Python.3.12 -e --source winget --accept-source-agreements --accept-package-agreements
    $python312 = & py -3.12 -c "import sys; print(sys.executable)"
}

if (-not (Test-Path $venvPython)) {
    Write-Host 'Creando backend/.venv...' -ForegroundColor Yellow
    & py -3.12 -m venv $venvRoot
}

Write-Host 'Instalando backend y herramientas de desarrollo...' -ForegroundColor Yellow
& $venvPython -m pip install --upgrade pip
& $venvPython -m pip install -e $backendRoot
& $venvPython -m pip install pytest ruff mypy httpx2

if ($null -eq (Get-Command npm.cmd -ErrorAction SilentlyContinue)) {
    throw "No se encuentra 'npm.cmd'. Instala Node.js LTS antes de ejecutar init.ps1."
}
if (-not $SkipFrontend) {
    Write-Host 'Instalando frontend...' -ForegroundColor Yellow
    Push-Location $frontendRoot
    try {
        npm.cmd install
    } finally {
        Pop-Location
    }
}

if ($null -eq (Get-Command ffmpeg -ErrorAction SilentlyContinue)) {
    if (-not $InstallSystemDependencies) {
        Write-Warning "FFmpeg no está en PATH. Ejecuta init.ps1 -InstallSystemDependencies para instalarlo mediante winget."
    } else {
        Require-Command 'winget' 'Instala App Installer de Microsoft.'
        winget install --id Gyan.FFmpeg -e --source winget --accept-source-agreements --accept-package-agreements
    }
}

New-Item -ItemType Directory -Path (Join-Path $repoRoot 'projects') -Force | Out-Null
Write-Host ''
Write-Host 'Setup completado.' -ForegroundColor Green
Write-Host 'Arranque local: .\scripts\start-dev.ps1 -ProjectRoot .\projects\<nombre>'
Write-Host 'Para instalar Python/FFmpeg automáticamente: .\scripts\init.ps1 -InstallSystemDependencies'
