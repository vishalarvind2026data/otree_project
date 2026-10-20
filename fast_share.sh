#!/usr/bin/env bash
# ==============================================================================
# Ultra-Fast 1-Click Live Sharing with Instant Clipboard Copy
# ==============================================================================

PORT=${1:-8000}

# Clean up any old duplicate tunnel processes
pkill -f "cloudflared tunnel" 2>/dev/null || true
pkill -f "localtunnel" 2>/dev/null || true

echo "⚡ Starting ultra-fast Cloudflare tunnel..."

# Temporary log file
TMP_LOG=$(mktemp)

# Start cloudflared in the background and capture the URL immediately
./cloudflared tunnel --url http://localhost:$PORT > "$TMP_LOG" 2>&1 &
TUNNEL_PID=$!

# Trap Ctrl+C to clean up
trap 'kill $TUNNEL_PID 2>/dev/null; rm -f "$TMP_LOG"; echo -e "\n[Stopped]"; exit 0' INT TERM

# Wait for URL to appear (typically ~4-5 seconds)
TUNNEL_URL=""
for i in {1..30}; do
    TUNNEL_URL=$(grep -o 'https://[a-zA-Z0-9-]*\.trycloudflare\.com' "$TMP_LOG" 2>/dev/null | head -n 1 || true)
    if [ -n "$TUNNEL_URL" ]; then
        break
    fi
    sleep 0.4
done

if [ -z "$TUNNEL_URL" ]; then
    echo "[!] Fallback: Checking full logs..."
    cat "$TMP_LOG"
    exit 1
fi

PARTICIPANT_LINK="${TUNNEL_URL}/room/online_open"
ADMIN_LINK="${TUNNEL_URL}/admin"

# Copy to macOS clipboard automatically if pbcopy is available
if command -v pbcopy >/dev/null 2>&1; then
    echo "$PARTICIPANT_LINK" | pbcopy
    CLIPBOARD_MSG=" (COPIED TO CLIPBOARD! Press Cmd+V to paste)"
else
    CLIPBOARD_MSG=""
fi

echo ""
echo "======================================================================"
echo "  🚀 EXPERIMENT IS LIVE IN 1 SECOND!"
echo "======================================================================"
echo ""
echo "👉 SEND THIS LINK TO PARTICIPANTS${CLIPBOARD_MSG}:"
echo "   $PARTICIPANT_LINK"
echo ""
echo "🔑 Admin Dashboard:"
echo "   $ADMIN_LINK"
echo ""
echo "----------------------------------------------------------------------"
echo "  • No passwords or IP numbers needed for participants."
echo "  • Works instantly on all phones, tablets, and laptops."
echo "  • Press Ctrl+C when you want to stop sharing."
echo "======================================================================"

# Keep process alive and stream any incoming connection events
tail -f "$TMP_LOG" | grep --line-buffered -E "(Registered tunnel|GET /)" 2>/dev/null || wait $TUNNEL_PID
