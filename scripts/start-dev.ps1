[CmdletBinding()]
param(
    [string]$ProjectRoot = "$PSScriptRoot\..\projects\proyecto_prueba_02",
    [int]$ApiPort = 8765,
    [int]$FrontendPort = 5173,
    [string]$ApiHost = "127.0.0.1",
    [string]$FrontendHost = "127.0.0.1",
    [string]$ApiBaseUrl = "http://127.0.0.1:8765",
    [string]$AllowedOrigin = "http://127.0.0.1:5173",
    [switch]$StopExisting
)

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$backendRoot = Join-Path $repoRoot 'backend'
$frontendRoot = Join-Path $repoRoot 'frontend'
$python = Join-Path $backendRoot '.venv\Scripts\python.exe'

if (-not (Test-Path $python)) {
    throw "No se encuentra el Python del backend: $python"
}
if (-not (Test-Path (Join-Path $frontendRoot 'package.json'))) {
    throw "No se encuentra el frontend Vite: $frontendRoot"
}
$ProjectRoot = (Resolve-Path $ProjectRoot).Path

function Get-ListeningProcess([int]$Port) {
    $connection = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($null -eq $connection) { return $null }
    return Get-Process -Id $connection.OwningProcess -ErrorAction SilentlyContinue
}

foreach ($port in @($ApiPort, $FrontendPort)) {
    $process = Get-ListeningProcess $port
    if ($null -ne $process) {
        if (-not $StopExisting) {
            throw "El puerto $port ya está ocupado por $($process.ProcessName) (PID $($process.Id)). Usa -StopExisting para detenerlo o reutiliza la instancia actual."
        }
        Write-Host "Deteniendo $($process.ProcessName) (PID $($process.Id)) en el puerto $port..." -ForegroundColor Yellow
        Stop-Process -Id $process.Id -Force
    }
}

Write-Host "Proyecto:  $ProjectRoot" -ForegroundColor Cyan
Write-Host "API:       $ApiHost`:$ApiPort" -ForegroundColor Cyan
Write-Host "Frontend:  $FrontendHost`:$FrontendPort" -ForegroundColor Cyan

$env:EDITORAGENT_ALLOWED_ORIGINS = $AllowedOrigin
$env:VITE_API_BASE = $ApiBaseUrl
$apiArgs = @('-m', 'editoragent.cli.main', 'api', 'serve', $ProjectRoot, '--workspace-root', $repoRoot, '--host', $ApiHost, '--port', "$ApiPort")
Start-Process -FilePath $python -ArgumentList $apiArgs -WorkingDirectory $backendRoot

$npm = (Get-Command npm.cmd -ErrorAction Stop).Source
$frontendArgs = @('--prefix', $frontendRoot, 'run', 'dev', '--', '--host', $FrontendHost, '--port', "$FrontendPort")
Start-Process -FilePath $npm -ArgumentList $frontendArgs -WorkingDirectory $repoRoot

Write-Host ''
Write-Host 'Stack iniciado en procesos separados.' -ForegroundColor Green
Write-Host 'Cierra las ventanas de API y Vite para detenerlo.' -ForegroundColor DarkGray
