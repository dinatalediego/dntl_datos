param(
    [int]$ApiPort = 8000,
    [int]$WebPort = 5173
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $RepoRoot ".venv\Scripts\python.exe"
$WebDir = Join-Path $RepoRoot "web"

if (-not (Test-Path $Python)) {
    throw "No existe .venv. Desde la raiz crea el entorno e instala el proyecto antes de ejecutar este launcher."
}

if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    throw "npm no esta disponible en PATH. Instala Node.js manualmente antes de ejecutar el Explorer."
}

Write-Host "DNTL Datos Explorer" -ForegroundColor Green
Write-Host "API: http://127.0.0.1:$ApiPort"
Write-Host "Web: http://127.0.0.1:$WebPort"

$ApiCommand = "Set-Location '$RepoRoot'; & '$Python' -m uvicorn dntl_datos.web_api:app --host 127.0.0.1 --port $ApiPort"
$WebCommand = "Set-Location '$WebDir'; npm run dev -- --host 127.0.0.1 --port $WebPort"

Start-Process powershell.exe -ArgumentList "-NoExit", "-Command", $ApiCommand
Start-Process powershell.exe -ArgumentList "-NoExit", "-Command", $WebCommand

Write-Host "Se abrieron dos terminales: API y PWA." -ForegroundColor Green
