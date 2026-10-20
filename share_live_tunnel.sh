#!/usr/bin/env bash
# ==============================================================================
# Share Live Tunnel Script (Instant Public Internet Link)
# ==============================================================================
set -e

PORT=${1:-8000}

echo "======================================================================"
echo "  oTree Instant Live Internet Exposer"
echo "======================================================================"
echo "This script creates a secure public HTTPS link to your local oTree"
echo "server so anyone on the internet can participate from anywhere in"
echo "the world on their phone or laptop."
echo ""

# Check if server is running on port 8000
if ! nc -z localhost $PORT 2>/dev/null; then
    echo "[!] Warning: No oTree server detected on http://localhost:$PORT."
    echo "    Please start the server first in another terminal with:"
    echo "    ./run_dev.sh"
    echo ""
    read -p "Press Enter to continue anyway or Ctrl+C to abort..."
fi

echo "[*] Connecting to secure public tunnel on port $PORT..."
echo "[*] When the URL is printed below, your participant link will be:"
echo "    https://<TUNNEL-DOMAIN>/room/online_open"
echo ""
echo "Press Ctrl+C at any time to stop public sharing."
echo "----------------------------------------------------------------------"

npx --yes localtunnel --port $PORT
