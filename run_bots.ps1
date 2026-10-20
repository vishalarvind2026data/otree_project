# PowerShell launcher for running bots
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

if (Test-Path "$ScriptDir\.venv\Scripts\Activate.ps1") {
    & "$ScriptDir\.venv\Scripts\Activate.ps1"
} elseif (Test-Path "$ScriptDir\..\.venv\Scripts\Activate.ps1") {
    & "$ScriptDir\..\.venv\Scripts\Activate.ps1"
}

python scripts/run_bots.py $args
