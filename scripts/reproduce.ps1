param(
    [ValidateSet("Full", "Committed")]
    [string]$Mode = "Full"
)

$ErrorActionPreference = "Stop"

$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$environmentPython = Join-Path $projectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $environmentPython)) {
    throw "The .venv environment is missing. Run ./scripts/setup.ps1 first."
}

function Invoke-ProjectPython {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Arguments)
    & $environmentPython @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Reproduction command failed: $($Arguments -join ' ')"
    }
}

Push-Location $projectRoot
try {
    if ($Mode -eq "Full") {
        Invoke-ProjectPython ".\scripts\acquire_cleveland_corral.py"
        Invoke-ProjectPython ".\scripts\inspect_cleveland_corral_archives.py"
        Invoke-ProjectPython ".\scripts\build_phase2_interim.py"
        Invoke-ProjectPython ".\scripts\verify_phase2_data.py"
        Invoke-ProjectPython ".\scripts\build_phase3_analysis.py"
        Invoke-ProjectPython ".\scripts\verify_phase3_outputs.py"
        Invoke-ProjectPython ".\scripts\build_phase4_analysis.py"
        Invoke-ProjectPython ".\scripts\verify_phase4_outputs.py"
        Invoke-ProjectPython ".\scripts\build_phase5_report.py" "--record-full-reproduction"
        Invoke-ProjectPython ".\scripts\execute_notebooks.py"
    }
    Invoke-ProjectPython ".\scripts\verify_phase5_outputs.py"
    & (Join-Path $PSScriptRoot "check.ps1")
    if ($LASTEXITCODE -ne 0) {
        throw "Repository checks failed."
    }
}
finally {
    Pop-Location
}

Write-Output "Reproduction completed successfully in $Mode mode."
