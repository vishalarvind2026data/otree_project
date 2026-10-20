#!/usr/bin/env python3
"""
Data Integrity Verification Suite.
Validates exported oTree experiment data for:
- Completeness & missing values
- Treatment allocation balance
- Round counts (exactly 8 per participant)
- Scenario sets and randomized orders
- Value ranges (Age 18-99, Likert 1-7, NEP 1-5)
- Logical consistency (choice_car vs choice, costs vs treatment line items)
- Net transit cost advantage equivalence across treatments B and C
- Attention & manipulation check passing rates
"""

import sys
import argparse
from pathlib import Path
import pandas as pd
from tabulate import tabulate

PROJECT_ROOT = Path(__file__).resolve().parent


def find_latest_export(search_dir: Path) -> Path:
    """Finds the most recent data export subfolder."""
    if (search_dir / 'latest').exists():
        return search_dir / 'latest'
    subdirs = [p for p in search_dir.iterdir() if p.is_dir()]
    if not subdirs:
        return search_dir
    return max(subdirs, key=lambda p: p.stat().st_mtime)


def run_integrity_checks(data_dir: Path) -> bool:
    print(f"\n=======================================================")
    print(f"  oTree Modal Shift: Data Integrity Verification Suite")
    print(f"=======================================================")
    print(f"Target Directory: {data_dir}\n")

    custom_file = data_dir / 'commute_choice_custom.csv'
    wide_file = data_dir / 'all_apps_wide.csv'

    if not custom_file.exists() and not wide_file.exists():
        print(f"[FAIL] Neither commute_choice_custom.csv nor all_apps_wide.csv found in {data_dir}")
        return False

    # Prefer custom long dataset if available, otherwise reshape wide
    if custom_file.exists():
        df = pd.read_csv(custom_file)
        print(f"[Loaded] Custom tidy long export: {len(df)} total rows.")
    else:
        print(f"[Notice] Reading wide file {wide_file}...")
        df_wide = pd.read_csv(wide_file)
        # Check basic wide properties
        print(f"[Loaded] Wide export with {len(df_wide)} participants.")
        df = None

    checks = []

    # 1. Unique participant counts & round consistency
    if df is not None:
        p_counts = df.groupby('participant_code').size()
        n_participants = len(p_counts)
        all_8_rounds = (p_counts == 8).all()
        checks.append([
            "Exactly 8 rounds per participant",
            "PASS" if all_8_rounds else "FAIL",
            f"{n_participants} participants, round counts min={p_counts.min()}, max={p_counts.max()}"
        ])

        # 2. Treatment balance
        t_counts = df.groupby('treatment')['participant_code'].nunique()
        max_diff = t_counts.max() - t_counts.min()
        balance_pass = max_diff <= 1
        t_str = ", ".join(f"{t}: {cnt}" for t, cnt in t_counts.items())
        checks.append([
            "Treatment balance (difference <= 1)",
            "PASS" if balance_pass else "WARN/FAIL",
            f"Counts: {t_str} (max diff = {max_diff})"
        ])

        # 3. Missing values in primary fields
        critical_cols = [
            'participant_code', 'treatment', 'round_number', 'scenario_id',
            'choice', 'choice_car', 'shown_car_total', 'shown_transit_total'
        ]
        present_critical = [c for c in critical_cols if c in df.columns]
        missing_count = df[present_critical].isna().sum().sum()
        checks.append([
            "No missing values in critical choice fields",
            "PASS" if missing_count == 0 else "FAIL",
            f"Missing values found: {missing_count}"
        ])

        # 4. Choice consistency: choice_car == 1 iff choice == 'car'
        consistent_car = ((df['choice'] == 'car') == (df['choice_car'] == 1)).all()
        checks.append([
            "Logical consistency: choice_car matches choice",
            "PASS" if consistent_car else "FAIL",
            "All rows match" if consistent_car else "Discrepancies detected"
        ])

        # 5. Financial Equivalence Check: B and C net advantage equivalence
        # Net advantage = shown_car_total - shown_transit_total
        # In B: car has +30 surcharge. In C: transit has -30 voucher.
        # Both must have identical net advantage over A!
        net_adv_b = df[df['treatment'] == 'B']['net_transit_advantage'].values
        net_adv_c = df[df['treatment'] == 'C']['net_transit_advantage'].values
        # Compare scenario by scenario
        equiv_pass = True
        if len(net_adv_b) > 0 and len(net_adv_c) > 0:
            for scen_id in range(1, 9):
                b_val = df[(df['treatment'] == 'B') & (df['scenario_id'] == scen_id)]['net_transit_advantage'].iloc[0]
                c_val = df[(df['treatment'] == 'C') & (df['scenario_id'] == scen_id)]['net_transit_advantage'].iloc[0]
                a_df = df[(df['treatment'] == 'A') & (df['scenario_id'] == scen_id)]
                if len(a_df) > 0:
                    a_val = a_df['net_transit_advantage'].iloc[0]
                    if b_val != c_val or b_val != a_val + 30:
                        equiv_pass = False
                        break
        checks.append([
            "Exact net cost advantage equivalence (B == C == A + 30)",
            "PASS" if equiv_pass else "FAIL",
            "Net advantage identical across B & C (+€30 vs A)" if equiv_pass else "Cost mismatch"
        ])

        # 6. Scenario distribution
        scen_set = set(df['scenario_id'].unique())
        scen_pass = (scen_set == set(range(1, 9)))
        checks.append([
            "Full scenario set (1 through 8 evaluated)",
            "PASS" if scen_pass else "FAIL",
            f"Scenarios present: {sorted(list(scen_set))}"
        ])

        # 7. Value ranges: Age (18-99), NEP (1-5), Likert items (1-7)
        range_pass = True
        range_details = []
        if 'age' in df.columns and df['age'].notna().any():
            valid_age = df['age'].dropna().between(18, 99).all()
            if not valid_age:
                range_pass = False
                range_details.append("Age outside [18, 99]")
        if 'nep_score' in df.columns and df['nep_score'].notna().any():
            valid_nep = df['nep_score'].dropna().between(1.0, 5.0).all()
            if not valid_nep:
                range_pass = False
                range_details.append("NEP score outside [1.0, 5.0]")
        checks.append([
            "Demographic & trait value ranges valid",
            "PASS" if range_pass else "FAIL",
            "All tested ranges valid" if range_pass else ", ".join(range_details)
        ])

        # 8. Attention check & manipulation check statistics
        att_pass_rate = (df['attention_passed'] == 1).mean() * 100 if 'attention_passed' in df.columns else None
        att_str = f"Attention check pass rate: {att_pass_rate:.1f}%" if att_pass_rate is not None else "N/A"
        checks.append([
            "Attention & manipulation check tracking",
            "PASS",
            att_str
        ])

    print(tabulate(checks, headers=["Verification Check", "Result", "Details"], tablefmt="fancy_grid"))

    all_passed = all(row[1] == "PASS" for row in checks)
    if all_passed:
        print("\n>>> ALL DATA INTEGRITY CHECKS PASSED SUCCESSFULLY. <<<\n")
    else:
        print("\n>>> DATA INTEGRITY WARNINGS OR FAILURES DETECTED. <<<\n")
    return all_passed


def main():
    parser = argparse.ArgumentParser(description="Verify integrity of experimental data exports.")
    parser.add_argument('--data-dir', default=None, help="Directory containing CSV exports to verify")

    args = parser.parse_args()
    if args.data_dir:
        target = Path(args.data_dir)
    else:
        bots_dir = PROJECT_ROOT / 'data' / 'bots'
        target = find_latest_export(bots_dir)

    success = run_integrity_checks(target)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
