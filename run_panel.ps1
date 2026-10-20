# PowerShell launcher for Streamlit control panel
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

if (Test-Path "$ScriptDir\.venv\Scripts\Activate.ps1") {
    & "$ScriptDir\.venv\Scripts\Activate.ps1"
} elseif (Test-Path "$ScriptDir\..\.venv\Scripts\Activate.ps1") {
    & "$ScriptDir\..\.venv\Scripts\Activate.ps1"
}

$port = if ($args[0]) { $args[0] } else { 8501 }
Write-Host "Starting Streamlit Control Panel on port $port..."
streamlit run app_control_panel.py --server.port $port
