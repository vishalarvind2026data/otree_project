#!/usr/bin/env python3
"""
CLI Utility to manage oTree rooms and participant label files.
Usage:
    python scripts/manage_rooms.py list
    python scripts/manage_rooms.py add lab_session_b --display "Secondary Lab Room" --labels 40 --prefix P --secure
    python scripts/manage_rooms.py remove lab_session_b
"""

import os
import sys
import json
import argparse
from pathlib import Path
from tabulate import tabulate

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ROOMS_FILE = PROJECT_ROOT / 'rooms.json'
ROOMS_DIR = PROJECT_ROOT / '_rooms'


def load_rooms():
    if not ROOMS_FILE.exists():
        return []
    try:
        with open(ROOMS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"[Error] Failed to read {ROOMS_FILE}: {e}")
        return []


def save_rooms(rooms):
    with open(ROOMS_FILE, 'w', encoding='utf-8') as f:
        json.dump(rooms, f, indent=2)


def cmd_list(args):
    rooms = load_rooms()
    if not rooms:
        print("No rooms configured in rooms.json.")
        return

    table = []
    for r in rooms:
        name = r.get('name')
        disp = r.get('display_name', '')
        lfile = r.get('participant_label_file', 'None (Open room)')
        count = 0
        if 'participant_label_file' in r:
            p = PROJECT_ROOT / r['participant_label_file']
            if p.exists():
                with open(p, 'r', encoding='utf-8') as lf:
                    count = len([line.strip() for line in lf if line.strip()])
            else:
                lfile += " [Missing File]"
        table.append([name, disp, lfile, count if count > 0 else 'N/A'])

    print("\nConfigured oTree Rooms:")
    print(tabulate(table, headers=["Room Name", "Display Name", "Label File", "Label Count"], tablefmt="fancy_grid"))
    print("\nNote: Any changes to rooms.json require restarting the oTree server.\n")


def cmd_add(args):
    rooms = load_rooms()
    if any(r['name'] == args.name for r in rooms):
        print(f"[Error] Room '{args.name}' already exists.")
        sys.exit(1)

    ROOMS_DIR.mkdir(parents=True, exist_ok=True)
    room_entry = {
        'name': args.name,
        'display_name': args.display or args.name
    }

    if args.labels and args.labels > 0:
        label_filename = f"{args.name}.txt"
        label_relpath = f"_rooms/{label_filename}"
        label_fullpath = ROOMS_DIR / label_filename

        prefix = args.prefix or 'P'
        digits = max(3, len(str(args.labels)))
        labels = [f"{prefix}{str(i).zfill(digits)}" for i in range(1, args.labels + 1)]

        with open(label_fullpath, 'w', encoding='utf-8') as f:
            for lbl in labels:
                f.write(f"{lbl}\n")

        room_entry['participant_label_file'] = label_relpath
        print(f"Generated {len(labels)} participant labels in {label_relpath} ({labels[0]} ... {labels[-1]})")

    rooms.append(room_entry)
    save_rooms(rooms)
    print(f"Successfully added room '{args.name}' to rooms.json.")
    print("[REMINDER] Please RESTART the oTree devserver or prodserver for new rooms to be loaded into memory.")


def cmd_remove(args):
    rooms = load_rooms()
    found = False
    new_rooms = []
    for r in rooms:
        if r['name'] == args.name:
            found = True
            if 'participant_label_file' in r:
                label_path = PROJECT_ROOT / r['participant_label_file']
                if label_path.exists():
                    try:
                        label_path.unlink()
                        print(f"Removed label file: {label_path}")
                    except Exception as e:
                        print(f"[Warning] Could not remove label file: {e}")
        else:
            new_rooms.append(r)

    if not found:
        print(f"[Error] Room '{args.name}' not found.")
        sys.exit(1)

    save_rooms(new_rooms)
    print(f"Successfully removed room '{args.name}' from rooms.json.")
    print("[REMINDER] Please RESTART the oTree server for room removals to take effect.")


def main():
    parser = argparse.ArgumentParser(description="Manage oTree experimental rooms and label files.")
    subparsers = parser.add_subparsers(dest='command', required=True)

    # list
    p_list = subparsers.add_parser('list', help="List configured rooms")
    p_list.set_defaults(func=cmd_list)

    # add
    p_add = subparsers.add_parser('add', help="Add a new room")
    p_add.add_argument('name', help="Internal room name (alphanumeric and underscores)")
    p_add.add_argument('--display', help="Display title shown to experimenters and participants")
    p_add.add_argument('--labels', type=int, default=0, help="Number of participant labels to generate")
    p_add.add_argument('--prefix', default='P', help="Prefix for participant labels (default: P)")
    p_add.add_argument('--secure', action='store_true', help="Use secure URLs requiring matching labels")
    p_add.set_defaults(func=cmd_add)

    # remove
    p_remove = subparsers.add_parser('remove', help="Remove an existing room")
    p_remove.add_argument('name', help="Name of the room to remove")
    p_remove.set_defaults(func=cmd_remove)

    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
