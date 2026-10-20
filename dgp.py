"""
Shared Data-Generating Process (DGP) and Simulation Engine
Used by:
- PlayerBot tests (commute_choice/tests.py, etc.)
- CLI bot runner (scripts/run_bots.py)
- Fallback simulator (scripts/simulate_fallback.py)
- Data verification and parameter recovery
"""

import os
import json
import math
import random
from typing import Dict, Any, List, Optional, Tuple

CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'bots_config.json')

def load_bots_config(preset_name: Optional[str] = None, overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Load configuration presets with optional parameter overrides."""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            cfg = json.load(f)
    else:
        cfg = {"active_preset": "default", "presets": {}}

    active = preset_name or os.getenv('BOT_PRESET', cfg.get('active_preset', 'default'))
    params = cfg.get('presets', {}).get(active, {
        "intercept": 0.65,
        "beta_B": -0.45,
        "beta_C": -0.25,
        "beta_nep_C": -0.15,
        "beta_car_B": 0.15,
        "cost_diff_coef": 0.025,
        "time_diff_coef": 0.040,
        "car_ownership_coef": 1.10,
        "nep_coef": -0.35,
        "patience_coef": -0.05,
        "risk_coef": 0.05,
        "inattentive_rate": 0.05,
        "latent_sigma": 0.80
    }).copy()

    # Environment overrides
    for key in ['BETA_B', 'BETA_C', 'BETA_NEP_C', 'BETA_CAR_B']:
        if os.getenv(key) is not None:
            params[key.lower()] = float(os.getenv(key))

    # Explicit function overrides
    if overrides:
        params.update(overrides)

    params['preset_name'] = active
    return params


# 8 Fixed Commute Scenarios
SCENARIOS = [
    {
        "id": 1,
        "distance_km": 8,
        "weather": "Sunny",
        "car_fuel_cost": 60,
        "car_parking_cost": 40,
        "car_time_min": 20,
        "transit_fare": 75,
        "transit_time_min": 30,
        "active_available": True,
        "active_time_min": 30,
        "description": "Short urban-fringe commute; active mobility (cycling) viable."
    },
    {
        "id": 2,
        "distance_km": 12,
        "weather": "Light Rain",
        "car_fuel_cost": 90,
        "car_parking_cost": 50,
        "car_time_min": 25,
        "transit_fare": 75,
        "transit_time_min": 38,
        "active_available": True,
        "active_time_min": 45,
        "description": "Suburban perimeter commute; light rain condition."
    },
    {
        "id": 3,
        "distance_km": 15,
        "weather": "Clear",
        "car_fuel_cost": 115,
        "car_parking_cost": 60,
        "car_time_min": 35,
        "transit_fare": 85,
        "transit_time_min": 45,
        "active_available": False,
        "active_time_min": 0,
        "description": "Medium suburban corridor; high vehicular congestion."
    },
    {
        "id": 4,
        "distance_km": 18,
        "weather": "Cloudy",
        "car_fuel_cost": 135,
        "car_parking_cost": 90,
        "car_time_min": 30,
        "transit_fare": 85,
        "transit_time_min": 48,
        "active_available": False,
        "active_time_min": 0,
        "description": "Suburban commute with elevated central parking charges."
    },
    {
        "id": 5,
        "distance_km": 22,
        "weather": "Clear",
        "car_fuel_cost": 165,
        "car_parking_cost": 50,
        "car_time_min": 35,
        "transit_fare": 95,
        "transit_time_min": 52,
        "active_available": False,
        "active_time_min": 0,
        "description": "Outer ring suburb to city center corridor."
    },
    {
        "id": 6,
        "distance_km": 26,
        "weather": "Rain",
        "car_fuel_cost": 195,
        "car_parking_cost": 65,
        "car_time_min": 45,
        "transit_fare": 95,
        "transit_time_min": 60,
        "active_available": False,
        "active_time_min": 0,
        "description": "Outer ring commute in adverse weather conditions."
    },
    {
        "id": 7,
        "distance_km": 30,
        "weather": "Clear",
        "car_fuel_cost": 225,
        "car_parking_cost": 80,
        "car_time_min": 50,
        "transit_fare": 110,
        "transit_time_min": 65,
        "active_available": False,
        "active_time_min": 0,
        "description": "Long-distance suburban radial commute."
    },
    {
        "id": 8,
        "distance_km": 35,
        "weather": "Foggy",
        "car_fuel_cost": 260,
        "car_parking_cost": 70,
        "car_time_min": 55,
        "transit_fare": 120,
        "transit_time_min": 72,
        "active_available": False,
        "active_time_min": 0,
        "description": "Exurban commute; high monthly fuel expense."
    }
]

SURCHARGE_AMOUNT = 30
VOUCHER_AMOUNT = 30

def get_scenario_costs(scenario: Dict[str, Any], treatment: str) -> Dict[str, Any]:
    """
    Computes exact displayed and net costs for a scenario under treatment A, B, or C.
    Enforces exact net financial equivalence:
    In B: car_total = fuel + parking + 30, transit_total = fare.
          Net transit advantage = (fuel + parking + 30) - fare = A + 30.
    In C: car_total = fuel + parking, transit_total = fare - 30.
          Net transit advantage = (fuel + parking) - (fare - 30) = A + 30.
    """
    fuel = scenario['car_fuel_cost']
    parking = scenario['car_parking_cost']
    base_car = fuel + parking
    base_transit = scenario['transit_fare']

    if treatment == 'A':  # Control
        car_total = base_car
        transit_total = base_transit
        surcharge = 0
        voucher = 0
        car_surcharge_line = ""
        transit_voucher_line = ""
    elif treatment == 'B':  # Loss / Carbon penalty on car
        car_total = base_car + SURCHARGE_AMOUNT
        transit_total = base_transit
        surcharge = SURCHARGE_AMOUNT
        voucher = 0
        car_surcharge_line = f"Carbon Pollution Surcharge: +€{SURCHARGE_AMOUNT}/month"
        transit_voucher_line = ""
    elif treatment == 'C':  # Gain / Green mobility bonus on transit
        car_total = base_car
        transit_total = base_transit - VOUCHER_AMOUNT
        surcharge = 0
        voucher = VOUCHER_AMOUNT
        car_surcharge_line = ""
        transit_voucher_line = f"Clean Mobility Pass Voucher: −€{VOUCHER_AMOUNT}/month"
    else:
        raise ValueError(f"Unknown treatment: {treatment}")

    # Per-trip calculations (assuming 22 working days × 2 trips/day = 44 trips/month)
    car_per_trip = round(car_total / 44, 2)
    transit_per_trip = round(transit_total / 44, 2)

    return {
        "car_fuel_cost": fuel,
        "car_parking_cost": parking,
        "car_surcharge": surcharge,
        "car_surcharge_line": car_surcharge_line,
        "shown_car_total": car_total,
        "car_per_trip": car_per_trip,
        "transit_fare": base_transit,
        "transit_voucher": voucher,
        "transit_voucher_line": transit_voucher_line,
        "shown_transit_total": transit_total,
        "transit_per_trip": transit_per_trip,
        "net_transit_advantage": car_total - transit_total
    }


def generate_bot_persona(participant_id: int, seed: Optional[int] = None) -> Dict[str, Any]:
    """Generates realistic, socio-demographically correlated persona and psychological traits."""
    rng = random.Random(seed if seed is not None else (participant_id * 7919 + 42))

    # Socio-demographics
    age = int(rng.gauss(41, 13))
    age = max(18, min(80, age))

    gender_draw = rng.random()
    if gender_draw < 0.49:
        gender = "Female"
    elif gender_draw < 0.97:
        gender = "Male"
    else:
        gender = "Non-binary"

    edu_draw = rng.random()
    if edu_draw < 0.22:
        education = "Secondary"
        edu_rank = 1
    elif edu_draw < 0.42:
        education = "Vocational"
        edu_rank = 2
    elif edu_draw < 0.74:
        education = "Bachelor"
        edu_rank = 3
    elif edu_draw < 0.96:
        education = "Master"
        edu_rank = 4
    else:
        education = "Doctorate"
        edu_rank = 5

    csp_choices = [
        "Executives & higher intellectual professions",
        "Intermediate professions",
        "Employees",
        "Workers",
        "Craftspeople / Shopkeepers / Business owners",
        "Students",
        "Retired",
        "Unemployed / Looking for work"
    ]
    if edu_rank >= 4:
        csp_weights = [0.45, 0.35, 0.10, 0.02, 0.03, 0.03, 0.01, 0.01]
    elif edu_rank == 3:
        csp_weights = [0.25, 0.40, 0.22, 0.05, 0.03, 0.03, 0.01, 0.01]
    else:
        csp_weights = [0.05, 0.20, 0.40, 0.23, 0.05, 0.02, 0.03, 0.02]
    occupation_csp = rng.choices(csp_choices, weights=csp_weights)[0]

    # Employment status
    if occupation_csp == "Students":
        employment_status = "Student"
    elif occupation_csp == "Retired":
        employment_status = "Retired"
    elif occupation_csp == "Unemployed / Looking for work":
        employment_status = "Not employed"
    elif occupation_csp == "Craftspeople / Shopkeepers / Business owners":
        employment_status = "Self-employed"
    else:
        employment_status = rng.choices(["Full-time", "Part-time"], weights=[0.85, 0.15])[0]

    # Residence type
    res_draw = rng.random()
    if res_draw < 0.12:
        residence_type = "City center"
        res_distance_base = 6
    elif res_draw < 0.46:
        residence_type = "Inner suburb (< 10 km)"
        res_distance_base = 12
    elif res_draw < 0.82:
        residence_type = "Outer suburb (10–25 km)"
        res_distance_base = 22
    else:
        residence_type = "Rural / Exurban (> 25 km)"
        res_distance_base = 32

    usual_commute_distance = max(4.0, round(rng.gauss(res_distance_base, 5.0), 1))

    # Car ownership: strongly suburban-dependent
    if residence_type == "City center":
        p_car = 0.38
    elif residence_type == "Inner suburb (< 10 km)":
        p_car = 0.68
    elif residence_type == "Outer suburb (10–25 km)":
        p_car = 0.90
    else:
        p_car = 0.96
    car_ownership = 1 if rng.random() < p_car else 0
    driving_license = 1 if (car_ownership == 1 or rng.random() < 0.85) else 0

    transit_pass = 1 if (car_ownership == 0 or rng.random() < 0.35) else 0
    bike_ownership = 1 if rng.random() < 0.62 else 0

    commute_days_per_week = rng.choices([3, 4, 5, 6], weights=[0.12, 0.20, 0.62, 0.06])[0]

    # Household income
    income_brackets = [
        "< €1,500",
        "€1,500–€2,499",
        "€2,500–€3,499",
        "€3,500–€4,999",
        "€5,000–€6,999",
        "≥ €7,000",
        "Prefer not to say"
    ]
    midpoints = [1000, 2000, 3000, 4250, 6000, 8500, 3500]
    if edu_rank >= 4:
        inc_weights = [0.03, 0.10, 0.22, 0.35, 0.20, 0.08, 0.02]
    elif edu_rank == 3:
        inc_weights = [0.08, 0.18, 0.30, 0.26, 0.12, 0.04, 0.02]
    else:
        inc_weights = [0.18, 0.32, 0.28, 0.14, 0.05, 0.01, 0.02]
    inc_idx = rng.choices(range(len(income_brackets)), weights=inc_weights)[0]
    income_bracket = income_brackets[inc_idx]
    income_numeric = midpoints[inc_idx]

    household_size = max(1, min(6, int(rng.gauss(2.4, 1.1))))
    children = max(0, min(household_size - 1, int(rng.gauss(0.8, 0.9)))) if household_size > 1 else 0

    # Behavioral traits
    risk_general = max(0, min(10, int(round(rng.gauss(5.2, 2.1)))))
    risk_driving = max(0, min(10, int(round(rng.gauss(4.7, 2.0)))))
    risk_switching_row = max(1, min(7, int(round(7 - (risk_general / 1.7)))))

    patience_general = max(0, min(10, int(round(rng.gauss(6.1, 2.0)))))
    patience_switching_row = max(1, min(7, int(round(patience_general / 1.8 + 1))))
    patience_index = round(patience_general / 10.0, 3)

    # Revised NEP Scale: 15 items, Dunlap et al. (2000)
    # Higher education & younger age correlate with slightly higher pro-ecological worldview
    nep_latent = 3.3 + 0.15 * (edu_rank - 3) - 0.01 * (age - 40) + rng.gauss(0, 0.5)
    nep_latent = max(1.5, min(4.8, nep_latent))

    nep_responses = {}
    nep_scored = []
    for item_num in range(1, 16):
        is_reverse = (item_num % 2 == 0)
        item_mu = (6.0 - nep_latent) if is_reverse else nep_latent
        raw_val = max(1, min(5, int(round(rng.gauss(item_mu, 0.85)))))
        nep_responses[f'nep_{item_num}'] = raw_val
        scored_val = (6 - raw_val) if is_reverse else raw_val
        nep_scored.append(scored_val)

    nep_score = round(sum(nep_scored) / 15.0, 3)

    # Inattention check: ~5% inattentive bots
    cfg = load_bots_config()
    is_inattentive = (rng.random() < cfg.get('inattentive_rate', 0.05))

    # Latent heterogeneity term u_i
    latent_sigma = cfg.get('latent_sigma', 0.80)
    u_i = rng.gauss(0, latent_sigma)

    return {
        "participant_id": participant_id,
        "age": age,
        "gender": gender,
        "education": education,
        "education_rank": edu_rank,
        "occupation_csp": occupation_csp,
        "employment_status": employment_status,
        "income_bracket": income_bracket,
        "income_numeric": income_numeric,
        "household_size": household_size,
        "children_in_household": children,
        "residence_type": residence_type,
        "usual_commute_distance": usual_commute_distance,
        "car_ownership": car_ownership,
        "driving_license": driving_license,
        "transit_pass": transit_pass,
        "bike_ownership": bike_ownership,
        "commute_days_per_week": commute_days_per_week,
        "risk_general": risk_general,
        "risk_driving": risk_driving,
        "risk_switching_row": risk_switching_row,
        "patience_general": patience_general,
        "patience_switching_row": patience_switching_row,
        "patience_index": patience_index,
        "nep_responses": nep_responses,
        "nep_score": nep_score,
        "is_inattentive": is_inattentive,
        "u_i": u_i
    }


def simulate_choice(
    persona: Dict[str, Any],
    scenario: Dict[str, Any],
    treatment: str,
    config: Optional[Dict[str, Any]] = None,
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Simulates a single commute choice using logit choice model with injected treatment effects.
    """
    cfg = config or load_bots_config()
    rng = random.Random(seed)

    costs = get_scenario_costs(scenario, treatment)
    car_cost = costs['shown_car_total']
    transit_cost = costs['shown_transit_total']
    car_time = scenario['car_time_min']
    transit_time = scenario['transit_time_min']
    active_avail = scenario['active_available']

    if persona.get('is_inattentive', False):
        # Inattentive bots select randomly with rapid decision time
        options = ['car', 'transit']
        if active_avail:
            options.append('active')
        choice = rng.choice(options)
        rt_ms = int(rng.uniform(600, 1800))
    else:
        # Attentive discrete choice logit
        intercept = cfg['intercept']
        cost_diff = (transit_cost - car_cost) / 100.0  # normalized per €100
        time_diff = (transit_time - car_time) / 10.0   # normalized per 10 min

        z = (
            intercept
            + cfg['cost_diff_coef'] * cost_diff * 100.0
            + cfg['time_diff_coef'] * time_diff * 10.0
            + cfg['car_ownership_coef'] * persona['car_ownership']
            + cfg['nep_coef'] * (persona['nep_score'] - 3.0)
            + cfg['patience_coef'] * (persona['patience_general'] - 5.0)
            + cfg['risk_coef'] * (persona['risk_general'] - 5.0)
            + persona['u_i']
        )

        # Injected treatment effects
        if treatment == 'B':
            # Loss framing: Carbon tax on car
            z += cfg['beta_B']
            # Heterogeneity: reactance among car owners
            z += cfg['beta_car_B'] * persona['car_ownership']
        elif treatment == 'C':
            # Gain framing: Mobility bonus voucher on transit
            z += cfg['beta_C']
            # Heterogeneity: pro-environmental sensitivity to green bonus
            z += cfg['beta_nep_C'] * (persona['nep_score'] - 3.0)

        # Logistic probability P(car)
        p_car = 1.0 / (1.0 + math.exp(-z))
        p_car = max(0.04, min(0.96, p_car))

        p_remaining = 1.0 - p_car
        if active_avail:
            # Active mobility available (<= 12 km)
            p_transit = p_remaining * 0.70
            p_active = p_remaining * 0.30
            weights = [p_car, p_transit, p_active]
            choice = rng.choices(['car', 'transit', 'active'], weights=weights)[0]
        else:
            p_transit = p_remaining
            weights = [p_car, p_transit]
            choice = rng.choices(['car', 'transit'], weights=weights)[0]

        # Realistic decision time (log-normal, slower if choices are close)
        difficulty = 1.0 - abs(p_car - 0.5) * 1.5
        base_log_rt = 8.1 + 0.3 * difficulty
        rt_ms = int(math.exp(rng.gauss(base_log_rt, 0.38)))
        rt_ms = max(900, min(30000, rt_ms))

    return {
        "scenario_id": scenario['id'],
        "treatment": treatment,
        "choice": choice,
        "choice_car": 1 if choice == 'car' else 0,
        "choice_transit": 1 if choice == 'transit' else 0,
        "choice_active": 1 if choice == 'active' else 0,
        "rt_ms": rt_ms,
        "shown_car_total": costs['shown_car_total'],
        "shown_transit_total": costs['shown_transit_total'],
        "car_fuel_cost": scenario['car_fuel_cost'],
        "car_parking_cost": scenario['car_parking_cost'],
        "car_surcharge": costs['car_surcharge'],
        "transit_fare": scenario['transit_fare'],
        "transit_voucher": costs['transit_voucher'],
        "net_transit_advantage": costs['net_transit_advantage']
    }


def simulate_post_task(persona: Dict[str, Any], treatment: str, seed: Optional[int] = None) -> Dict[str, Any]:
    """Simulates manipulation check, attention check, and post-task policy attitudes."""
    rng = random.Random(seed)

    is_inattentive = persona.get('is_inattentive', False)

    # Manipulation check: Which line item was shown?
    options = [
        "A Carbon Pollution Surcharge on the car option",
        "A Clean Mobility Pass Voucher on the public transit option",
        "No extra surcharge or voucher",
        "I do not remember"
    ]
    if is_inattentive:
        manip_seen = rng.choice(options)
        attention_passed = 1 if rng.random() < 0.20 else 0
    else:
        # Attentive participants pass attention check (must select 1: Strongly disagree)
        attention_passed = 1
        if treatment == 'A':
            manip_seen = "No extra surcharge or voucher" if rng.random() < 0.92 else rng.choice(options)
        elif treatment == 'B':
            manip_seen = "A Carbon Pollution Surcharge on the car option" if rng.random() < 0.94 else rng.choice(options)
        elif treatment == 'C':
            manip_seen = "A Clean Mobility Pass Voucher on the public transit option" if rng.random() < 0.94 else rng.choice(options)
        else:
            manip_seen = "I do not remember"

    # Attitudinal Likert items (1 to 7)
    nep = persona['nep_score']
    car_own = persona['car_ownership']

    # Acceptability and fairness of carbon tax (lower for car owners, higher for high NEP)
    tax_base = 3.8 + 0.9 * (nep - 3.0) - 1.2 * car_own
    tax_fairness = max(1, min(7, int(round(rng.gauss(tax_base, 1.2)))))
    tax_effectiveness = max(1, min(7, int(round(rng.gauss(tax_base + 0.3, 1.2)))))

    # Acceptability and fairness of green voucher (broadly popular)
    bonus_base = 5.2 + 0.6 * (nep - 3.0) - 0.2 * car_own
    bonus_fairness = max(1, min(7, int(round(rng.gauss(bonus_base, 1.0)))))
    bonus_effectiveness = max(1, min(7, int(round(rng.gauss(bonus_base + 0.2, 1.0)))))

    support_transition_funds = max(1, min(7, int(round(rng.gauss(4.6 + 0.8 * (nep - 3.0), 1.1)))))

    # Reactance / Coerciveness (perceived coerciveness higher for treatment B, especially car owners)
    reactance_base = 3.2 + (1.4 if treatment == 'B' else 0.0) + 0.8 * car_own
    perceived_coerciveness = max(1, min(7, int(round(rng.gauss(reactance_base, 1.2)))))

    # Abstract policy support
    support_carbon_tax = max(1, min(7, int(round(rng.gauss(tax_base, 1.3)))))
    support_mobility_bonus = max(1, min(7, int(round(rng.gauss(bonus_base, 1.0)))))

    return {
        "manip_seen": manip_seen,
        "attention_passed": attention_passed,
        "tax_fairness": tax_fairness,
        "tax_effectiveness": tax_effectiveness,
        "bonus_fairness": bonus_fairness,
        "bonus_effectiveness": bonus_effectiveness,
        "support_transition_funds": support_transition_funds,
        "perceived_coerciveness": perceived_coerciveness,
        "support_carbon_tax": support_carbon_tax,
        "support_mobility_bonus": support_mobility_bonus,
        "comments": ""
    }
