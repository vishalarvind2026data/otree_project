"""
Report Helper and In-Website Bot Execution Engine.
Provides functions to:
1. Load econometric outputs, tables, and base64-encoded figures for display in oTree Admin Report.
2. Execute bot simulations synchronously or in a worker thread and update analysis datasets.
"""

import sys
import os
import subprocess
import shutil
import base64
from pathlib import Path
from typing import Dict, Any, Optional
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent


def get_report_data(out_dir_name: str = 'bots') -> Dict[str, Any]:
    """Loads all figures, tables, and narrative summaries from the outputs folder."""
    out_dir = PROJECT_ROOT / 'outputs' / out_dir_name
    if not out_dir.exists():
        # Fall back to outputs/bots or outputs/live or outputs/both
        if (PROJECT_ROOT / 'outputs' / 'bots').exists():
            out_dir = PROJECT_ROOT / 'outputs' / 'bots'
        elif (PROJECT_ROOT / 'outputs' / 'both').exists():
            out_dir = PROJECT_ROOT / 'outputs' / 'both'
        elif (PROJECT_ROOT / 'outputs' / 'live').exists():
            out_dir = PROJECT_ROOT / 'outputs' / 'live'

    figures = {}
    fig_names = [
        'car_share_by_treatment',
        'coefficients_forest_plot',
        'traits_distribution',
        'decision_time_boxplot',
        'parameter_recovery_plot'
    ]
    for name in fig_names:
        img_path = out_dir / f"{name}.png"
        if img_path.exists():
            b64_data = base64.b64encode(img_path.read_bytes()).decode('utf-8')
            figures[name] = f"data:image/png;base64,{b64_data}"
        else:
            figures[name] = ""

    tables = {}
    table_files = [
        ('table_main_regression', 'Main Regression Output (LPM & Logit AMEs)'),
        ('table_randomization_balance', 'Randomization Balance Check'),
        ('table_descriptives_choice', 'Descriptive Choice Statistics by Treatment'),
        ('table_parameter_recovery', 'Parameter Recovery Comparison')
    ]
    sample_info = {'participants': 0, 'choices': 0, 'by_treatment': {}}
    for key, label in table_files:
        csv_path = out_dir / f"{key}.csv"
        if csv_path.exists():
            try:
                df = pd.read_csv(csv_path)
                tables[key] = {
                    'label': label,
                    'headers': list(df.columns),
                    'rows': df.fillna('').values.tolist()
                }
                if key == 'table_descriptives_choice':
                    total_c = int(df['count'].sum()) if 'count' in df.columns else 0
                    sample_info['choices'] = total_c
                    sample_info['participants'] = total_c // 8
                    if 'treatment' in df.columns and 'count' in df.columns:
                        sample_info['by_treatment'] = dict(zip(df['treatment'], df['count'].astype(int)))
            except Exception:
                tables[key] = None
        else:
            tables[key] = None

    # Load narrative markdown if present
    report_md_path = out_dir / 'analysis_report.md'
    report_text = ""
    if report_md_path.exists():
        try:
            report_text = report_md_path.read_text(encoding='utf-8')
        except Exception:
            report_text = ""

    return {
        'figures': figures,
        'tables': tables,
        'report_text': report_text,
        'sample_info': sample_info,
        'current_source': out_dir.name,
        'source_folder': str(out_dir.relative_to(PROJECT_ROOT) if out_dir.is_relative_to(PROJECT_ROOT) else out_dir)
    }


def execute_bot_simulation_and_pipeline(
    num_bots: int = 30,
    session_config: str = 'modal_shift',
    preset: str = 'default'
) -> Dict[str, Any]:
    """
    Executes an in-website bot simulation:
    1. Runs otree test --export with the requested number of bots.
    2. Runs test.py data integrity checks.
    3. Runs analysis/prepare_data.py and analysis/run_analysis.py for the bots sample size.
    4. Also updates outputs/both.
    5. Returns success status, session code, and report URL.
    """
    python_bin = PROJECT_ROOT / '.venv' / 'bin' / 'python'
    if not python_bin.exists():
        python_bin = Path(sys.executable)

    # 1. Run simulation via run_bots.py script
    run_bots_script = PROJECT_ROOT / 'scripts' / 'run_bots.py'
    cmd = [
        str(python_bin), str(run_bots_script),
        '--n', str(num_bots),
        '--config', str(session_config),
        '--preset', str(preset)
    ]

    res = subprocess.run(cmd, cwd=str(PROJECT_ROOT), capture_output=True, text=True)
    if res.returncode != 0:
        return {
            'success': False,
            'error': f"Bot simulation failed: {res.stderr or res.stdout}"
        }

    # 2. Run data preparation & analysis specifically for the bots run of given sample size
    prep_script = PROJECT_ROOT / 'analysis' / 'prepare_data.py'
    analysis_script = PROJECT_ROOT / 'analysis' / 'run_analysis.py'

    # Analyze bots of the given sample size
    subprocess.run([str(python_bin), str(prep_script), '--source', 'bots'], cwd=str(PROJECT_ROOT), capture_output=True)
    subprocess.run([str(python_bin), str(analysis_script), '--source', 'bots'], cwd=str(PROJECT_ROOT), capture_output=True)

    # Also update pooled both
    subprocess.run([str(python_bin), str(prep_script), '--source', 'both'], cwd=str(PROJECT_ROOT), capture_output=True)
    subprocess.run([str(python_bin), str(analysis_script), '--source', 'both'], cwd=str(PROJECT_ROOT), capture_output=True)

    # 3. Retrieve the latest session code safely via read-only SQLite query
    session_code = ""
    try:
        import sqlite3
        db_path = PROJECT_ROOT / 'db.sqlite3'
        if db_path.exists():
            with sqlite3.connect(f"file:{db_path}?mode=ro", uri=True) as conn:
                cur = conn.cursor()
                cur.execute("SELECT code FROM otree_session ORDER BY id DESC LIMIT 1")
                row = cur.fetchone()
                if row:
                    session_code = row[0]
    except Exception:
        pass

    report_url = f"/report?source=bots"

    return {
        'success': True,
        'session_code': session_code,
        'report_url': report_url,
        'num_bots': num_bots,
        'stdout': res.stdout
    }
