#!/usr/bin/env bash
# ==============================================================================
# All-In-One oTree Live Hosting Script
# Single bash command that starts server, creates tunnel, & opens admin page
# ==============================================================================
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "======================================================================"
echo "  🚀 Starting oTree Live Public Hosting..."
echo "======================================================================"

# 1. Clean up any previous server or tunnel processes
echo "[1/4] Freeing port 8000 and cleaning up old processes..."
pkill -f "cloudflared tunnel" 2>/dev/null || true
pkill -f "localtunnel" 2>/dev/null || true
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
sleep 1

# 2. Activate Python Virtual Environment
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
elif [ -f "../.venv/bin/activate" ]; then
    source ../.venv/bin/activate
fi

# 3. Start oTree server in the background
echo "[2/4] Starting oTree server on http://127.0.0.1:8000..."
SERVER_LOG=$(mktemp)
otree prodserver 0.0.0.0:8000 > "$SERVER_LOG" 2>&1 &
SERVER_PID=$!

# Wait for server to respond
SERVER_READY=0
for i in {1..20}; do
    if curl -s -o /dev/null http://127.0.0.1:8000/ 2>/dev/null; then
        SERVER_READY=1
        break
    fi
    sleep 0.3
done

if [ "$SERVER_READY" -eq 0 ]; then
    echo "[!] Error starting oTree server. Logs:"
    cat "$SERVER_LOG"
    kill -9 $SERVER_PID 2>/dev/null || true
    rm -f "$SERVER_LOG"
    exit 1
fi
echo "      ✓ Local server running!"

# 4. Start Cloudflare Tunnel
echo "[3/4] Establishing secure public HTTPS tunnel..."
TUNNEL_LOG=$(mktemp)
./cloudflared tunnel --url http://127.0.0.1:8000 > "$TUNNEL_LOG" 2>&1 &
TUNNEL_PID=$!

# Trap Ctrl+C to cleanly shut down both processes
cleanup() {
    echo ""
    echo "[*] Stopping live hosting..."
    kill -9 $TUNNEL_PID 2>/dev/null || true
    kill -9 $SERVER_PID 2>/dev/null || true
    rm -f "$SERVER_LOG" "$TUNNEL_LOG"
    echo "[✓] Offline. All services stopped."
    exit 0
}
trap cleanup INT TERM

# Wait for public URL (typically 4-6 seconds)
TUNNEL_URL=""
for i in {1..30}; do
    TUNNEL_URL=$(grep -o 'https://[a-zA-Z0-9-]*\.trycloudflare\.com' "$TUNNEL_LOG" 2>/dev/null | head -n 1 || true)
    if [ -n "$TUNNEL_URL" ]; then
        break
    fi
    sleep 0.4
done

if [ -z "$TUNNEL_URL" ]; then
    echo "[!] Could not obtain Cloudflare tunnel URL. Logs:"
    cat "$TUNNEL_LOG"
    cleanup
fi

PARTICIPANT_LINK="${TUNNEL_URL}/room/online_open"
ADMIN_LINK="${TUNNEL_URL}/admin"

# Copy participant link to macOS clipboard
if command -v pbcopy >/dev/null 2>&1; then
    echo "$PARTICIPANT_LINK" | pbcopy
    CLIP_NOTE=" (Copied to Clipboard! Just press Cmd+V to paste)"
else
    CLIP_NOTE=""
fi

# Automatically open admin page in browser
echo "[4/4] Opening Admin Dashboard in your browser..."
open "$ADMIN_LINK" 2>/dev/null || open "http://127.0.0.1:8000/admin" 2>/dev/null || true

echo ""
echo "======================================================================"
echo "  🎉 YOUR EXPERIMENT IS NOW 100% LIVE ON THE INTERNET!"
echo "======================================================================"
echo ""
echo "👉 PARTICIPANT LINK${CLIP_NOTE}:"
echo "   $PARTICIPANT_LINK"
echo ""
echo "🔑 ADMIN DASHBOARD:"
echo "   $ADMIN_LINK"
echo "   (Username: admin | Password: admin)"
echo ""
echo "💻 LOCAL ACCESS (ON THIS MAC):"
echo "   http://127.0.0.1:8000/admin"
echo ""
echo "----------------------------------------------------------------------"
echo "  • Participants can open the link on any phone or laptop anywhere."
echo "  • No codes or passwords required for participants."
echo "  • All data saves in real-time to your local database."
echo "  • To STOP hosting, press Ctrl+C in this terminal."
echo "======================================================================"
echo ""
echo "Watching live connections (Press Ctrl+C to stop)..."

# Keep alive and print live request logs
tail -f "$SERVER_LOG" 2>/dev/null || wait $SERVER_PID
