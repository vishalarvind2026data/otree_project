#!/usr/bin/env python3
"""
Data preparation pipeline for Modal Shift & Carbon Taxation Experiment.
Reads raw oTree CSV exports from data/live/ and data/bots/,
cleans, standardizes schemas, derives econometric variables,
tags data source (live vs bots), and produces:
- data/processed/analysis_long.csv (choice-level panel: participant × round)
- data/processed/analysis_participant.csv (cross-sectional participant level)
"""

import os
import sys
import argparse
from pathlib import Path
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / 'data'
PROCESSED_DIR = DATA_DIR / 'processed'


def find_export_files(folder: Path):
    """Recursively locates custom long exports or wide exports."""
    custom_files = list(folder.glob('**/commute_choice_custom.csv'))
    wide_files = list(folder.glob('**/all_apps_wide.csv'))
    return custom_files, wide_files


def clean_long_data(df: pd.DataFrame, source_tag: str) -> pd.DataFrame:
    """Standardizes column types and constructs derived analytical variables."""
    df = df.copy()
    df['source'] = source_tag

    # Ensure required columns
    df['treatment'] = df['treatment'].astype(str).str.upper()
    df['treat_A'] = (df['treatment'] == 'A').astype(int)
    df['treat_B'] = (df['treatment'] == 'B').astype(int)
    df['treat_C'] = (df['treatment'] == 'C').astype(int)

    # Outcome variables
    if 'choice_car' not in df.columns:
        df['choice_car'] = (df['choice'] == 'car').astype(int)
    if 'choice_transit' not in df.columns:
        df['choice_transit'] = (df['choice'] == 'transit').astype(int)
    if 'choice_active' not in df.columns:
        df['choice_active'] = (df['choice'] == 'active').astype(int)

    # Reaction time
    if 'rt_ms' in df.columns:
        df['rt_ms'] = pd.to_numeric(df['rt_ms'], errors='coerce').fillna(2500)
        df['log_rt'] = np.log(np.maximum(df['rt_ms'], 100))
        df['fast_decision'] = (df['rt_ms'] < 1500).astype(int)

    # Socio-demographics & traits
    if 'age' in df.columns:
        df['age'] = pd.to_numeric(df['age'], errors='coerce')
        df['young'] = (df['age'] < 35).astype(float)

    if 'car_ownership' in df.columns:
        if df['car_ownership'].dtype == object:
            df['owns_car'] = df['car_ownership'].astype(str).str.contains('Yes', case=False, na=False).astype(int)
        else:
            df['owns_car'] = pd.to_numeric(df['car_ownership'], errors='coerce').fillna(0).astype(int)
    else:
        df['owns_car'] = 0

    if 'income_numeric' in df.columns:
        df['income_numeric'] = pd.to_numeric(df['income_numeric'], errors='coerce').fillna(3500)
        df['income_k'] = df['income_numeric'] / 1000.0

    if 'nep_score' in df.columns:
        df['nep_score'] = pd.to_numeric(df['nep_score'], errors='coerce')
        df['nep_centered'] = df['nep_score'] - 3.0

    if 'patience_index' in df.columns:
        df['patience_index'] = pd.to_numeric(df['patience_index'], errors='coerce')

    if 'attention_passed' in df.columns:
        df['attention_passed'] = pd.to_numeric(df['attention_passed'], errors='coerce').fillna(1).astype(int)
    else:
        df['attention_passed'] = 1

    # Cost & time differentials
    if 'shown_car_total' in df.columns and 'shown_transit_total' in df.columns:
        df['cost_diff'] = df['shown_transit_total'] - df['shown_car_total']
    if 'transit_time_min' in df.columns and 'car_time_min' in df.columns:
        df['time_diff'] = df['transit_time_min'] - df['car_time_min']

    return df


def prepare_datasets(source: str = 'both'):
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    dfs = []

    # 1. Process Bots Data
    if source in ('bots', 'both'):
        bots_dir = DATA_DIR / 'bots'
        custom_files, wide_files = find_export_files(bots_dir)
        latest_file = bots_dir / 'latest' / 'commute_choice_custom.csv'
        if latest_file.exists():
            latest_custom = latest_file
        elif custom_files:
            latest_custom = max(custom_files, key=lambda p: p.stat().st_mtime)
        else:
            latest_custom = None

        if latest_custom:
            print(f"[Prepare] Reading bots data from: {latest_custom}")
            df_b = pd.read_csv(latest_custom)
            df_b_clean = clean_long_data(df_b, 'bots')
            dfs.append(df_b_clean)
        else:
            print(f"[Warning] No custom export found in {bots_dir}")

    # 2. Process Live Data
    if source in ('live', 'both'):
        live_dir = DATA_DIR / 'live'
        custom_files, wide_files = find_export_files(live_dir)
        latest_live = live_dir / 'latest' / 'commute_choice_custom.csv'
        if latest_live.exists():
            latest_custom = latest_live
        elif custom_files:
            latest_custom = max(custom_files, key=lambda p: p.stat().st_mtime)
        else:
            latest_custom = None

        if latest_custom:
            print(f"[Prepare] Reading live data from: {latest_custom}")
            df_l = pd.read_csv(latest_custom)
            df_l_clean = clean_long_data(df_l, 'live')
            dfs.append(df_l_clean)
        else:
            print(f"[Notice] No live data exports found in {live_dir}")

    if not dfs:
        print("[Error] No data found to process.")
        return None, None

    df_combined = pd.concat(dfs, ignore_index=True)

    # Filter complete participants (exactly 8 choice rounds)
    p_round_counts = df_combined.groupby('participant_code')['round_number'].nunique()
    valid_participants = p_round_counts[p_round_counts == 8].index
    dropped_count = len(p_round_counts) - len(valid_participants)
    if dropped_count > 0:
        print(f"[Filter] Dropped {dropped_count} incomplete participant sessions.")

    df_long = df_combined[df_combined['participant_code'].isin(valid_participants)].copy()

    # Aggregate to participant-level dataset
    # Mean car share across 8 rounds
    part_agg = df_long.groupby('participant_code').agg({
        'session_code': 'first',
        'source': 'first',
        'is_bot': 'first',
        'treatment': 'first',
        'treat_A': 'first',
        'treat_B': 'first',
        'treat_C': 'first',
        'choice_car': 'mean',
        'choice_transit': 'mean',
        'choice_active': 'mean',
        'rt_ms': 'mean',
        'age': 'first',
        'gender': 'first',
        'education': 'first',
        'occupation_csp': 'first',
        'employment_status': 'first',
        'income_bracket': 'first',
        'income_numeric': 'first',
        'household_size': 'first',
        'children_in_household': 'first',
        'residence_type': 'first',
        'usual_commute_distance': 'first',
        'owns_car': 'first',
        'driving_license': 'first',
        'transit_pass': 'first',
        'bike_ownership': 'first',
        'commute_days_per_week': 'first',
        'risk_general': 'first',
        'risk_driving': 'first',
        'risk_switching_row': 'first',
        'patience_general': 'first',
        'patience_switching_row': 'first',
        'patience_index': 'first',
        'nep_score': 'first',
        'manip_seen': 'first',
        'attention_passed': 'first',
        'tax_fairness': 'first',
        'tax_effectiveness': 'first',
        'bonus_fairness': 'first',
        'bonus_effectiveness': 'first',
        'support_transition_funds': 'first',
        'perceived_coerciveness': 'first',
        'support_carbon_tax': 'first',
        'support_mobility_bonus': 'first'
    }).reset_index()

    part_agg.rename(columns={
        'choice_car': 'share_car',
        'choice_transit': 'share_transit',
        'choice_active': 'share_active',
        'rt_ms': 'mean_rt_ms'
    }, inplace=True)

    # Save to data/processed
    out_long_path = PROCESSED_DIR / 'analysis_long.csv'
    out_part_path = PROCESSED_DIR / 'analysis_participant.csv'
    df_long.to_csv(out_long_path, index=False)
    part_agg.to_csv(out_part_path, index=False)

    print(f"\n[Saved] Processed Long Data:        {out_long_path} ({len(df_long)} rows)")
    print(f"[Saved] Processed Participant Data: {out_part_path} ({len(part_agg)} participants)\n")

    return df_long, part_agg


def main():
    parser = argparse.ArgumentParser(description="Prepare experimental data for econometric analysis.")
    parser.add_argument('--source', choices=['live', 'bots', 'both'], default='both', help="Data source to clean")
    args = parser.parse_args()
    prepare_datasets(args.source)


if __name__ == '__main__':
    main()
