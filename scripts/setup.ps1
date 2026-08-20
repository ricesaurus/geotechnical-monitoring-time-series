$ErrorActionPreference = "Stop"

$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$environmentPath = Join-Path $projectRoot ".venv"
$environmentPython = Join-Path $environmentPath "Scripts\python.exe"

if (-not (Test-Path -LiteralPath $environmentPython)) {
    $systemPython = Get-Command python -ErrorAction SilentlyContinue
    if ($null -eq $systemPython) {
        throw "Python was not found. Install Python 3.12 and rerun this script."
    }

    & $systemPython.Source -m venv $environmentPath
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $environmentPython)) {
        throw "Failed to create the virtual environment at $environmentPath."
    }
}

& $environmentPython -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) {
    throw "Failed to upgrade pip."
}

& $environmentPython -m pip install -e "${projectRoot}[dev]"
if ($LASTEXITCODE -ne 0) {
    throw "Failed to install the project dependencies."
}

Write-Output "Environment ready: $environmentPath"
Write-Output "Activate it with: ./.venv/Scripts/Activate.ps1"
