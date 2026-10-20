#!/usr/bin/env bash
set -e
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
elif [ -f "../.venv/bin/activate" ]; then
    source ../.venv/bin/activate
fi

export PATH="$DIR/.venv/bin:$PATH"
PORT=${1:-8501}
echo "Starting Streamlit Control Panel on port $PORT..."
streamlit run app_control_panel.py --server.port "$PORT"
