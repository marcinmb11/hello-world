$ErrorActionPreference = "Stop"

$projectRoot = Resolve-Path (Join-Path (Split-Path $MyInvocation.MyCommand.Path) "..")
$venvPath = Join-Path $projectRoot ".venv"

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Error "[bootstrap] Python interpreter not found. Ensure python is available in PATH."
}

if (-not (Test-Path $venvPath)) {
    Write-Host "[bootstrap] Creating virtual environment in $venvPath"
    python -m venv $venvPath
}
else {
    Write-Host "[bootstrap] Reusing existing virtual environment in $venvPath"
}

$pipPath = Join-Path $venvPath "Scripts/pip.exe"
& $pipPath install --upgrade pip
& $pipPath install -r (Join-Path $projectRoot "requirements.txt")

Write-Host "`n[bootstrap] Environment ready."
Write-Host "[bootstrap] Activate it with: `"$venvPath\Scripts\activate`""
Write-Host "[bootstrap] Run the web UI with: flask --app app run"
Write-Host "[bootstrap] Or execute the CLI demo with: python example_usage.py"
