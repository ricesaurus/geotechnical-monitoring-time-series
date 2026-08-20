$ErrorActionPreference = "Stop"

$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$environmentPython = Join-Path $projectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $environmentPython)) {
    throw "The .venv environment is missing. Run ./scripts/setup.ps1 first."
}

& $environmentPython -m ruff check $projectRoot
if ($LASTEXITCODE -ne 0) {
    throw "Ruff checks failed."
}

& $environmentPython -m pytest $projectRoot
if ($LASTEXITCODE -ne 0) {
    throw "Tests failed."
}

& $environmentPython (Join-Path $PSScriptRoot "check_environment.py")
if ($LASTEXITCODE -ne 0) {
    throw "Environment verification failed."
}
