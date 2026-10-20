#!/usr/bin/env python3
"""
CLI Utility to generate room-wide and per-participant experiment URLs.
Supports CSV output, printable HTML sheets, QR code image generation,
and direct REST API session creation.

Usage:
    python scripts/generate_links.py --base-url http://localhost:8000 --room lab_session --n 40 --format csv
    python scripts/generate_links.py --base-url http://localhost:8000 --room lab_session --format html
    python scripts/generate_links.py --base-url http://localhost:8000 --room lab_session --format qr
    python scripts/generate_links.py --base-url http://localhost:8000 --create-session modal_shift --n 30
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional
import requests
import qrcode
from tabulate import tabulate
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUTS_DIR = PROJECT_ROOT / 'outputs' / 'links'
ROOMS_FILE = PROJECT_ROOT / 'rooms.json'


def get_room_labels(room_name: str, n_requested: Optional[int] = None) -> List[str]:
    """Finds or constructs participant labels for a specified room."""
    if not ROOMS_FILE.exists():
        print(f"[Error] {ROOMS_FILE} not found.")
        sys.exit(1)

    with open(ROOMS_FILE, 'r', encoding='utf-8') as f:
        rooms = json.load(f)

    target_room = next((r for r in rooms if r['name'] == room_name), None)
    if not target_room:
        print(f"[Error] Room '{room_name}' not found in rooms.json.")
        sys.exit(1)

    labels = []
    if 'participant_label_file' in target_room:
        lpath = PROJECT_ROOT / target_room['participant_label_file']
        if lpath.exists():
            with open(lpath, 'r', encoding='utf-8') as lf:
                labels = [line.strip() for line in lf if line.strip()]

    if not labels:
        count = n_requested or 20
        labels = [f"P{str(i).zfill(3)}" for i in range(1, count + 1)]
    elif n_requested and n_requested < len(labels):
        labels = labels[:n_requested]

    return labels


def export_csv(links: List[Dict[str, str]], out_path: Path):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write("participant_label,url\n")
        for row in links:
            f.write(f"{row['label']},{row['url']}\n")
    print(f"[Saved] CSV links exported to: {out_path}")


def export_html(room_name: str, room_url: str, links: List[Dict[str, str]], out_path: Path):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    cards_html = ""
    for row in links:
        cards_html += f"""
        <div class="card-slip">
            <div class="slip-header">
                <strong>Room: {room_name}</strong>
                <span class="label-badge">{row['label']}</span>
            </div>
            <div class="slip-body">
                <p class="url-text">{row['url']}</p>
                <div class="qr-placeholder" data-url="{row['url']}"></div>
                <div class="instructions">Enter the exact URL above or scan your personal QR code at your terminal.</div>
            </div>
        </div>
        """

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>oTree Participant Access Slips - {room_name}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            color: #1e293b;
        }}
        h2 {{
            border-bottom: 2px solid #0f172a;
            padding-bottom: 8px;
        }}
        .room-info {{
            margin-bottom: 20px;
            font-size: 14px;
            background: #f1f5f9;
            padding: 10px 15px;
            border-radius: 6px;
        }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 15px;
        }}
        .card-slip {{
            border: 2px dashed #94a3b8;
            padding: 12px 16px;
            border-radius: 8px;
            page-break-inside: avoid;
            background: #ffffff;
        }}
        .slip-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid #e2e8f0;
            padding-bottom: 6px;
            margin-bottom: 8px;
        }}
        .label-badge {{
            background: #2563eb;
            color: #ffffff;
            padding: 3px 8px;
            border-radius: 4px;
            font-weight: bold;
        }}
        .url-text {{
            font-family: monospace;
            font-size: 12px;
            word-break: break-all;
            color: #0369a1;
            margin: 6px 0;
        }}
        .instructions {{
            font-size: 11px;
            color: #64748b;
        }}
        @media print {{
            body {{ margin: 0; }}
            .no-print {{ display: none; }}
        }}
    </style>
</head>
<body>
    <div class="no-print" style="margin-bottom: 15px;">
        <button onclick="window.print()" style="padding: 8px 16px; font-weight: bold; cursor: pointer;">Print Participant Access Slips</button>
    </div>
    <h2>Modal Shift Experiment: Participant Access Slips</h2>
    <div class="room-info">
        <strong>Room:</strong> {room_name} &nbsp;|&nbsp;
        <strong>Room-wide URL:</strong> <a href="{room_url}">{room_url}</a> &nbsp;|&nbsp;
        <strong>Total Participants:</strong> {len(links)}
    </div>
    <div class="grid">
        {cards_html}
    </div>
</body>
</html>"""

    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"[Saved] Printable HTML slips exported to: {out_path}")


def export_qr(room_name: str, room_url: str, links: List[Dict[str, str]], out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    # 1. Room-wide QR
    img_room = qrcode.make(room_url)
    img_room.save(out_dir / f"{room_name}_room_qr.png")

    # 2. Per-participant QRs
    for row in links:
        img_p = qrcode.make(row['url'])
        img_p.save(out_dir / f"qr_{row['label']}.png")
    print(f"[Saved] Generated {len(links) + 1} QR codes in: {out_dir}")


def create_session_rest(base_url: str, rest_key: str, config_name: str, n_participants: int, room_name: Optional[str] = None):
    """Creates a session via oTree REST API and returns participant initialize links."""
    endpoint = f"{base_url.rstrip('/')}/api/sessions"
    headers = {
        "otree-rest-key": rest_key,
        "Content-Type": "application/json"
    }
    payload = {
        "session_config_name": config_name,
        "num_participants": n_participants
    }
    if room_name:
        payload["room_name"] = room_name

    print(f"Connecting to REST API at {endpoint}...")
    try:
        resp = requests.post(endpoint, headers=headers, json=payload, timeout=10)
        if resp.status_code not in (200, 201):
            print(f"[Error] REST API responded with status {resp.status_code}: {resp.text}")
            sys.exit(1)

        data = resp.json()
        session_code = data.get('code')
        session_wide_url = f"{base_url.rstrip('/')}/join/{session_code}"
        print(f"\n[Success] Created session with code: {session_code}")
        print(f"Session Wide URL: {session_wide_url}\n")

        # In oTree REST API, participants list is returned or accessible
        participants = data.get('participants', [])
        if participants:
            rows = []
            for p in participants:
                p_code = p.get('code')
                p_label = p.get('label', '')
                p_url = f"{base_url.rstrip('/')}/InitializeParticipant/{p_code}"
                rows.append([p_code, p_label, p_url])
            print(tabulate(rows, headers=["Participant Code", "Label", "Direct Access URL"], tablefmt="fancy_grid"))

        return data
    except Exception as e:
        print(f"[Error] Failed to connect to oTree REST API: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Generate oTree room links, printable access sheets, QR codes, and REST sessions.")
    parser.add_argument('--base-url', default=os.getenv('OTREE_BASE_URL', 'http://localhost:8000'), help="Base URL of oTree server")
    parser.add_argument('--room', default='lab_session', help="Name of room from rooms.json")
    parser.add_argument('--n', type=int, default=None, help="Number of participant links to generate")
    parser.add_argument('--format', choices=['csv', 'html', 'qr', 'table'], default='table', help="Output format")
    parser.add_argument('--create-session', metavar='CONFIG', help="Create a live session via oTree REST API with given config name")
    parser.add_argument('--rest-key', default=os.getenv('OTREE_REST_KEY', 'secret_rest_key_12345'), help="oTree REST API security key")

    args = parser.parse_args()
    base = args.base_url.rstrip('/')

    if args.create_session:
        create_session_rest(base, args.rest_key, args.create_session, args.n or 30, args.room if args.room != 'none' else None)
        return

    labels = get_room_labels(args.room, args.n)
    room_wide_url = f"{base}/room/{args.room}/"
    links = []
    for lbl in labels:
        p_url = f"{base}/room/{args.room}/?participant_label={lbl}"
        links.append({'label': lbl, 'url': p_url})

    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

    if args.format == 'csv':
        export_csv(links, OUTPUTS_DIR / f"{args.room}_links.csv")
    elif args.format == 'html':
        export_html(args.room, room_wide_url, links, OUTPUTS_DIR / f"{args.room}_links.html")
    elif args.format == 'qr':
        export_qr(args.room, room_wide_url, links, OUTPUTS_DIR / f"qr_{args.room}")
    else:  # table
        print(f"\nRoom-Wide Access URL: {room_wide_url}\n")
        table_rows = [[l['label'], l['url']] for l in links[:15]]
        print(tabulate(table_rows, headers=["Participant Label", "Direct Access Link"], tablefmt="fancy_grid"))
        if len(links) > 15:
            print(f"... and {len(links) - 15} more participant links.")
        print(f"\nTotal Links: {len(links)}. To export full files use --format csv, html, or qr.\n")


if __name__ == '__main__':
    main()
