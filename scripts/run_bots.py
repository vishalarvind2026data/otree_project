#!/usr/bin/env python3
"""
CLI Bot Runner:
Generates simulated participants, runs them through the experimental workflow,
exports tidy wide and long datasets, writes ground-truth parameters,
and verifies data integrity.

Usage:
    python scripts/run_bots.py --n 150 --config modal_shift --preset default --seed 123
"""

import os
import sys
import json
import time
import shutil
import argparse
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
import pandas as pd
from tabulate import tabulate

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
import dgp
from scripts.simulate_fallback import run_fallback_simulation


def run_bots(
    n_bots: int = 150,
    config: str = 'modal_shift',
    preset: str = 'default',
    seed: int = 123,
    out_dir: Optional[Path] = None,
    overrides: Optional[dict] = None
) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    target_dir = out_dir or (PROJECT_ROOT / 'data' / 'bots' / f"run_{timestamp}")
    target_dir.mkdir(parents=True, exist_ok=True)

    # 1. Resolve and store ground-truth parameters
    params = dgp.load_bots_config(preset, overrides)
    true_params_doc = {
        'timestamp': timestamp,
        'config': config,
        'n_bots': n_bots,
        'seed': seed,
        'preset': preset,
        'true_parameters': params
    }
    with open(target_dir / 'true_parameters.json', 'w', encoding='utf-8') as f:
        json.dump(true_params_doc, f, indent=2)

    print(f"\n==================================================")
    print(f"  oTree Modal Shift: Running Bot Simulation Engine")
    print(f"==================================================")
    print(f"Target Participants: {n_bots}")
    print(f"Session Config:      {config}")
    print(f"Parameter Preset:    {preset}")
    print(f"Random Seed:         {seed}")
    print(f"Output Directory:    {target_dir}\n")

    # Set environment variables for child processes / bot execution
    env = os.environ.copy()
    env['BOT_PRESET'] = preset
    env['PYTHONHASHSEED'] = str(seed)
    env['PATH'] = f"{PROJECT_ROOT}/.venv/bin:{env.get('PATH', '')}"
    env['DATABASE_URL'] = f"sqlite:///{target_dir}/bot_simulation.sqlite3"
    if overrides:
        for k, v in overrides.items():
            env[k.upper()] = str(v)

    otree_bin = PROJECT_ROOT / '.venv' / 'bin' / 'otree'
    cmd = [
        str(otree_bin),
        'test',
        '--export',
        str(target_dir),
        config,
        str(n_bots)
    ]

    use_fallback = False
    print(f"Executing: {' '.join(cmd)}")
    try:
        proc = subprocess.run(cmd, cwd=str(PROJECT_ROOT), env=env, capture_output=True, text=True, timeout=180)
        if proc.returncode != 0:
            print(f"[Warning] otree test finished with return code {proc.returncode}.")
            print(f"Stderr snippet:\n{proc.stderr[-500:] if proc.stderr else proc.stdout[-500:]}")
            use_fallback = True
        else:
            print("[Success] oTree test completed successfully.")
    except Exception as e:
        print(f"[Warning] otree test invocation failed ({e}). Engaging pure-Python fallback simulator.")
        use_fallback = True

    # Check generated files
    wide_file = target_dir / 'all_apps_wide.csv'
    custom_file = target_dir / 'commute_choice_custom.csv'

    if use_fallback or not wide_file.exists() or wide_file.stat().st_size == 0:
        print("\nEngaging Fallback Simulator (scripts/simulate_fallback.py)...")
        run_fallback_simulation(n_bots, target_dir, preset=preset, seed=seed, overrides=overrides)

    # Ensure files contain only the current session's participants and is_bot=1
    latest_sess = None
    if custom_file.exists():
        try:
            df_custom = pd.read_csv(custom_file)
            if 'session_code' in df_custom.columns and len(df_custom) > 0:
                latest_sess = df_custom['session_code'].iloc[-1]
                df_custom = df_custom[df_custom['session_code'] == latest_sess].copy()
            df_custom['is_bot'] = 1
            df_custom.to_csv(custom_file, index=False)
        except Exception as e:
            print(f"[Warning] Could not update custom file: {e}")

    if wide_file.exists():
        try:
            df_wide = pd.read_csv(wide_file)
            if latest_sess and 'session.code' in df_wide.columns:
                df_wide = df_wide[df_wide['session.code'] == latest_sess].copy()
            if 'participant.is_bot' not in df_wide.columns:
                df_wide['participant.is_bot'] = 1
            if 'participant._is_bot' not in df_wide.columns:
                df_wide['participant._is_bot'] = 1
            df_wide.to_csv(wide_file, index=False)
        except Exception as e:
            print(f"[Warning] Could not update wide file: {e}")

    # Also make a convenient symlink or copy to data/bots/latest
    latest_dir = PROJECT_ROOT / 'data' / 'bots' / 'latest'
    if latest_dir.exists():
        shutil.rmtree(latest_dir)
    shutil.copytree(target_dir, latest_dir)

    print(f"\n[Data Export Complete] Files saved in:\n  - {target_dir}\n  - {latest_dir}")

    # Run data integrity checks
    integrity_script = PROJECT_ROOT / 'test.py'
    py_exec = PROJECT_ROOT / '.venv' / 'bin' / 'python'
    if not py_exec.exists():
        py_exec = Path(sys.executable)

    if integrity_script.exists():
        print("\nRunning automated data integrity verification...")
        res = subprocess.run([str(py_exec), str(integrity_script), '--data-dir', str(target_dir)], capture_output=True, text=True)
        print(res.stdout)
        if res.returncode != 0 and res.stderr:
            print(f"[Integrity Warnings]: {res.stderr}")

    # Automatically compile econometric models and visualizations for this specific bot sample
    prep_script = PROJECT_ROOT / 'analysis' / 'prepare_data.py'
    analysis_script = PROJECT_ROOT / 'analysis' / 'run_analysis.py'
    if prep_script.exists() and analysis_script.exists():
        print(f"\nCompiling econometric models and visualizations for N = {n_bots} bots...")
        subprocess.run([str(py_exec), str(prep_script), '--source', 'bots'], cwd=str(PROJECT_ROOT), capture_output=True)
        subprocess.run([str(py_exec), str(analysis_script), '--source', 'bots'], cwd=str(PROJECT_ROOT), capture_output=True)
        subprocess.run([str(py_exec), str(prep_script), '--source', 'both'], cwd=str(PROJECT_ROOT), capture_output=True)
        subprocess.run([str(py_exec), str(analysis_script), '--source', 'both'], cwd=str(PROJECT_ROOT), capture_output=True)
        print(f"[Econometrics Complete] Updated outputs/bots/ with sample size N = {n_bots}.")

    return target_dir


def main():
    parser = argparse.ArgumentParser(description="Run simulated bot participants in oTree and export data.")
    parser.add_argument('--n', type=int, default=150, help="Number of bot participants to generate (default: 150)")
    parser.add_argument('--config', default='modal_shift', help="Session config name (default: modal_shift)")
    parser.add_argument('--preset', default='default', choices=['default', 'null_effects', 'gain_stronger', 'strong_loss'], help="Bot response preset")
    parser.add_argument('--seed', type=int, default=123, help="Random seed (default: 123)")
    parser.add_argument('--out', default=None, help="Output directory path")
    parser.add_argument('--beta_B', type=float, default=None, help="Override for beta_B (Loss effect)")
    parser.add_argument('--beta_C', type=float, default=None, help="Override for beta_C (Gain effect)")
    parser.add_argument('--beta_nep_C', type=float, default=None, help="Override for NEP x Gain interaction")
    parser.add_argument('--beta_car_B', type=float, default=None, help="Override for Car Ownership x Loss interaction")

    args = parser.parse_args()

    overrides = {}
    if args.beta_B is not None:
        overrides['beta_B'] = args.beta_B
    if args.beta_C is not None:
        overrides['beta_C'] = args.beta_C
    if args.beta_nep_C is not None:
        overrides['beta_nep_C'] = args.beta_nep_C
    if args.beta_car_B is not None:
        overrides['beta_car_B'] = args.beta_car_B

    out_p = Path(args.out) if args.out else None
    run_bots(
        n_bots=args.n,
        config=args.config,
        preset=args.preset,
        seed=args.seed,
        out_dir=out_p,
        overrides=overrides if overrides else None
    )


if __name__ == '__main__':
    main()
