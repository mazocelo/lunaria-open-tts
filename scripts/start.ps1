$envFile = Join-Path $PSScriptRoot "..\\.env"

if (-not (Test-Path $envFile)) {
  Write-Error "Arquivo .env nao encontrado. Copie .env.example para .env antes de iniciar."
  exit 1
}

uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload
