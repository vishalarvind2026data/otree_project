#!/usr/bin/env python3
"""
Pure-Python Fallback Simulator.
Imports dgp.py and generates datasets matching the exact schema of oTree exports:
- all_apps_wide.csv
- commute_choice_custom.csv (tidy long format)
- true_parameters.json
"""

import os
import sys
import csv
import json
import random
from pathlib import Path
from typing import Dict, Any, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
import dgp


def run_fallback_simulation(
    n_participants: int,
    output_dir: Path,
    preset: str = 'default',
    seed: int = 123,
    overrides: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Generates synthetic experimental data using the DGP choice engine."""
    output_dir.mkdir(parents=True, exist_ok=True)
    cfg = dgp.load_bots_config(preset, overrides)
    rng = random.Random(seed)

    # Save true parameters
    true_params = {
        'preset': preset,
        'seed': seed,
        'n_participants': n_participants,
        'parameters': cfg
    }
    with open(output_dir / 'true_parameters.json', 'w', encoding='utf-8') as f:
        json.dump(true_params, f, indent=2)

    # Balanced treatment allocation
    treatments_pool = ['A', 'B', 'C'] * (n_participants // 3 + 1)
    treatments = treatments_pool[:n_participants]
    rng.shuffle(treatments)

    session_code = f"s_bot_{seed}"

    long_rows = []
    wide_rows = []

    for i in range(1, n_participants + 1):
        p_code = f"bot_{str(i).zfill(4)}"
        t = treatments[i - 1]
        p_seed = seed * 1000 + i
        persona = dgp.generate_bot_persona(i, seed=p_seed)

        # Scenarios presentation order
        scen_order = list(range(1, 9))
        rng.shuffle(scen_order)

        wide_entry = {
            'participant.id_in_session': i,
            'participant.code': p_code,
            'participant.label': f"BOT_{str(i).zfill(3)}",
            'participant._is_bot': 1,
            'participant.is_bot': 1,
            'participant.treatment': t,
            'session.code': session_code,
            'session.config.name': 'modal_shift',
            # Demographics
            'survey_demographics.1.player.age': persona['age'],
            'survey_demographics.1.player.gender': persona['gender'],
            'survey_demographics.1.player.education': persona['education'],
            'survey_demographics.1.player.occupation_csp': persona['occupation_csp'],
            'survey_demographics.1.player.employment_status': persona['employment_status'],
            'survey_demographics.1.player.income_bracket': persona['income_bracket'],
            'survey_demographics.1.player.household_size': persona['household_size'],
            'survey_demographics.1.player.children_in_household': persona['children_in_household'],
            'survey_demographics.1.player.residence_type': persona['residence_type'],
            'survey_demographics.1.player.usual_commute_distance_km': persona['usual_commute_distance'],
            'survey_demographics.1.player.car_ownership': "Yes, personal car" if persona['car_ownership'] == 1 else "No car",
            'survey_demographics.1.player.driving_license': "Yes" if persona['driving_license'] == 1 else "No",
            'survey_demographics.1.player.transit_pass_ownership': "Yes" if persona['transit_pass'] == 1 else "No",
            'survey_demographics.1.player.bike_ownership': "Yes" if persona['bike_ownership'] == 1 else "No",
            'survey_demographics.1.player.commute_days_per_week': persona['commute_days_per_week'],
            # Traits
            'survey_traits.1.player.risk_general': persona['risk_general'],
            'survey_traits.1.player.risk_driving': persona['risk_driving'],
            'survey_traits.1.player.risk_switching_row': persona['risk_switching_row'],
            'survey_traits.1.player.patience_general': persona['patience_general'],
            'survey_traits.1.player.patience_switching_row': persona['patience_switching_row'],
            'survey_traits.1.player.patience_index': persona['patience_index'],
            'survey_traits.1.player.nep_score': persona['nep_score']
        }

        for k in range(1, 16):
            wide_entry[f'survey_traits.1.player.nep_{k}'] = persona['nep_responses'][f'nep_{k}']

        # Commute rounds
        for r_num in range(1, 9):
            scen_id = scen_order[r_num - 1]
            scenario = dgp.SCENARIOS[scen_id - 1]
            r_seed = p_seed * 10 + r_num
            choice_data = dgp.simulate_choice(persona, scenario, t, config=cfg, seed=r_seed)

            # Wide columns
            prefix = f"commute_choice.{r_num}.player."
            wide_entry[prefix + 'choice'] = choice_data['choice']
            wide_entry[prefix + 'choice_car'] = choice_data['choice_car']
            wide_entry[prefix + 'choice_transit'] = choice_data['choice_transit']
            wide_entry[prefix + 'choice_active'] = choice_data['choice_active']
            wide_entry[prefix + 'rt_ms'] = choice_data['rt_ms']
            wide_entry[prefix + 'scenario_id'] = scen_id
            wide_entry[prefix + 'treatment'] = t
            wide_entry[prefix + 'shown_car_total'] = choice_data['shown_car_total']
            wide_entry[prefix + 'shown_transit_total'] = choice_data['shown_transit_total']

            # Long format entry
            long_entry = {
                'session_code': session_code,
                'participant_code': p_code,
                'is_bot': 1,
                'treatment': t,
                'round_number': r_num,
                'scenario_id': scen_id,
                'distance_km': scenario['distance_km'],
                'weather': scenario['weather'],
                'car_fuel_cost': scenario['car_fuel_cost'],
                'car_parking_cost': scenario['car_parking_cost'],
                'car_surcharge': choice_data['car_surcharge'],
                'shown_car_total': choice_data['shown_car_total'],
                'transit_fare': scenario['transit_fare'],
                'transit_voucher': choice_data['transit_voucher'],
                'shown_transit_total': choice_data['shown_transit_total'],
                'net_transit_advantage': choice_data['net_transit_advantage'],
                'car_time_min': scenario['car_time_min'],
                'transit_time_min': scenario['transit_time_min'],
                'active_available': 1 if scenario['active_available'] else 0,
                'active_time_min': scenario['active_time_min'],
                'choice': choice_data['choice'],
                'choice_car': choice_data['choice_car'],
                'choice_transit': choice_data['choice_transit'],
                'choice_active': choice_data['choice_active'],
                'rt_ms': choice_data['rt_ms'],
                # Demographics
                'age': persona['age'],
                'gender': persona['gender'],
                'education': persona['education'],
                'occupation_csp': persona['occupation_csp'],
                'employment_status': persona['employment_status'],
                'income_bracket': persona['income_bracket'],
                'income_numeric': persona['income_numeric'],
                'household_size': persona['household_size'],
                'children_in_household': persona['children_in_household'],
                'residence_type': persona['residence_type'],
                'usual_commute_distance': persona['usual_commute_distance'],
                'car_ownership': persona['car_ownership'],
                'driving_license': persona['driving_license'],
                'transit_pass': persona['transit_pass'],
                'bike_ownership': persona['bike_ownership'],
                'commute_days_per_week': persona['commute_days_per_week'],
                # Traits
                'risk_general': persona['risk_general'],
                'risk_driving': persona['risk_driving'],
                'risk_switching_row': persona['risk_switching_row'],
                'patience_general': persona['patience_general'],
                'patience_switching_row': persona['patience_switching_row'],
                'patience_index': persona['patience_index'],
                'nep_score': persona['nep_score']
            }
            long_rows.append(long_entry)

        # Post-task
        post_data = dgp.simulate_post_task(persona, t, seed=p_seed * 11)
        wide_entry['post_task.1.player.manip_seen'] = post_data['manip_seen']
        wide_entry['post_task.1.player.attention_passed'] = post_data['attention_passed']
        wide_entry['post_task.1.player.tax_fairness'] = post_data['tax_fairness']
        wide_entry['post_task.1.player.tax_effectiveness'] = post_data['tax_effectiveness']
        wide_entry['post_task.1.player.bonus_fairness'] = post_data['bonus_fairness']
        wide_entry['post_task.1.player.bonus_effectiveness'] = post_data['bonus_effectiveness']
        wide_entry['post_task.1.player.support_transition_funds'] = post_data['support_transition_funds']
        wide_entry['post_task.1.player.perceived_coerciveness'] = post_data['perceived_coerciveness']
        wide_entry['post_task.1.player.support_carbon_tax'] = post_data['support_carbon_tax']
        wide_entry['post_task.1.player.support_mobility_bonus'] = post_data['support_mobility_bonus']
        wide_rows.append(wide_entry)

        # Update long entries for this participant with post-task fields
        for entry in long_rows[-8:]:
            entry.update(post_data)

    # Write all_apps_wide.csv
    if wide_rows:
        wide_fields = list(wide_rows[0].keys())
        with open(output_dir / 'all_apps_wide.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=wide_fields)
            writer.writeheader()
            writer.writerows(wide_rows)

    # Write commute_choice_custom.csv
    if long_rows:
        long_fields = list(long_rows[0].keys())
        with open(output_dir / 'commute_choice_custom.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=long_fields)
            writer.writeheader()
            writer.writerows(long_rows)

    print(f"[Fallback Simulation] Generated {n_participants} participants ({len(long_rows)} choices) in {output_dir}")
    return true_params


if __name__ == '__main__':
    out = PROJECT_ROOT / 'data' / 'bots' / 'test_fallback'
    run_fallback_simulation(30, out)
