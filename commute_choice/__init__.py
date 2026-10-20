from otree.api import *
import dgp

doc = """
Commute Choice Experiment: 8 repeated choice scenarios across randomized treatments.
Treatment A: Control
Treatment B: Loss / Carbon Penalty (+€30 on car)
Treatment C: Gain / Green Bonus (-€30 on transit)
Both B and C maintain strictly identical net transit advantage (+€30 vs control).
"""


class C(BaseConstants):
    NAME_IN_URL = 'commute'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 8
    SURCHARGE_AMOUNT = dgp.SURCHARGE_AMOUNT
    VOUCHER_AMOUNT = dgp.VOUCHER_AMOUNT
    SCENARIOS = dgp.SCENARIOS


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    choice = models.StringField(
        choices=[
            ['car', 'Private Car'],
            ['transit', 'Public Transit'],
            ['active', 'Active Mobility (Bicycle / Walking)']
        ],
        widget=widgets.RadioSelect,
        label="Select your preferred commute mode for this journey:"
    )
    choice_car = models.IntegerField(initial=0)
    choice_transit = models.IntegerField(initial=0)
    choice_active = models.IntegerField(initial=0)
    rt_ms = models.IntegerField(initial=0)
    scenario_id = models.IntegerField()
    shown_car_total = models.IntegerField()
    shown_transit_total = models.IntegerField()
    treatment = models.StringField()


class ChoicePage(Page):
    form_model = 'player'
    form_fields = ['choice', 'rt_ms']

    @staticmethod
    def vars_for_template(player: Player):
        participant = player.participant
        treatment = participant.treatment

        # Retrieve randomized scenario order
        order = participant.scenario_order
        scenario_idx = order[player.round_number - 1]
        scenario = dgp.SCENARIOS[scenario_idx - 1]

        # Calculate exact itemised costs
        costs = dgp.get_scenario_costs(scenario, treatment)

        # Store round metadata into player model
        player.scenario_id = scenario['id']
        player.treatment = treatment
        player.shown_car_total = costs['shown_car_total']
        player.shown_transit_total = costs['shown_transit_total']

        return {
            'scenario': scenario,
            'costs': costs,
            'treatment': treatment,
            'round_num': player.round_number,
            'total_rounds': C.NUM_ROUNDS,
            'active_available': scenario['active_available']
        }

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        # Set dummy indicators
        player.choice_car = 1 if player.choice == 'car' else 0
        player.choice_transit = 1 if player.choice == 'transit' else 0
        player.choice_active = 1 if player.choice == 'active' else 0


page_sequence = [ChoicePage]


def vars_for_admin_report(subsession: Subsession):
    """Generates session-level summary statistics for the oTree Admin Report tab."""
    session = subsession.session
    players = subsession.get_players()

    # Aggregate across all rounds in session
    treatments = ['A', 'B', 'C']
    stats = {}
    for t in treatments:
        stats[t] = {
            'n_participants': 0,
            'car_choices': 0,
            'total_choices': 0,
            'rt_sum': 0
        }

    bot_stats = {'car': 0, 'total': 0, 'n': 0}
    live_stats = {'car': 0, 'total': 0, 'n': 0}

    seen_participants = set()

    for p in players:
        part = p.participant
        t = getattr(part, 'treatment', 'A')
        is_bot = getattr(part, 'is_bot', False) or getattr(part, '_is_bot', False)

        if part.code not in seen_participants:
            seen_participants.add(part.code)
            if t in stats:
                stats[t]['n_participants'] += 1
            if is_bot:
                bot_stats['n'] += 1
            else:
                live_stats['n'] += 1

        # Check all round decisions
        for r_player in p.in_all_rounds():
            if r_player.choice:
                stats[t]['total_choices'] += 1
                if r_player.choice == 'car':
                    stats[t]['car_choices'] += 1
                if r_player.rt_ms:
                    stats[t]['rt_sum'] += r_player.rt_ms

                if is_bot:
                    bot_stats['total'] += 1
                    if r_player.choice == 'car':
                        bot_stats['car'] += 1
                else:
                    live_stats['total'] += 1
                    if r_player.choice == 'car':
                        live_stats['car'] += 1

    summary = []
    for t in treatments:
        s = stats[t]
        pct_car = (s['car_choices'] / s['total_choices'] * 100) if s['total_choices'] > 0 else 0.0
        mean_rt = (s['rt_sum'] / s['total_choices']) if s['total_choices'] > 0 else 0
        summary.append({
            'treatment': t,
            'n_participants': s['n_participants'],
            'total_choices': s['total_choices'],
            'car_share_pct': round(pct_car, 1),
            'mean_rt_ms': int(mean_rt)
        })

    bot_car_pct = round((bot_stats['car'] / bot_stats['total'] * 100), 1) if bot_stats['total'] > 0 else 0.0
    live_car_pct = round((live_stats['car'] / live_stats['total'] * 100), 1) if live_stats['total'] > 0 else 0.0

    # Generate real-time live session visualizations directly from this session's actual data
    live_visuals = {'has_data': False, 'figures': {}, 'total_choices': 0, 'n_participants': 0}
    try:
        import live_report_visualizer
        live_visuals = live_report_visualizer.generate_live_session_visualizations(session, players)
    except Exception as e:
        print(f"[Warning] Failed generating live session visuals: {e}")

    # Load benchmark econometric models for population reference
    benchmark_data = {}
    try:
        import report_helper
        benchmark_data = report_helper.get_report_data('bots')
    except Exception:
        pass

    return {
        'session_code': session.code,
        'summary': summary,
        'bot_stats': bot_stats,
        'live_stats': live_stats,
        'bot_car_pct': bot_car_pct,
        'live_car_pct': live_car_pct,
        'live_visuals': live_visuals,
        'benchmark_data': benchmark_data,
    }


def custom_export(players):
    """Exports tidy long-format dataset with participant and scenario variables joined."""
    # Header
    yield [
        'session_code',
        'participant_code',
        'is_bot',
        'treatment',
        'round_number',
        'scenario_id',
        'distance_km',
        'weather',
        'car_fuel_cost',
        'car_parking_cost',
        'car_surcharge',
        'shown_car_total',
        'transit_fare',
        'transit_voucher',
        'shown_transit_total',
        'net_transit_advantage',
        'car_time_min',
        'transit_time_min',
        'active_available',
        'active_time_min',
        'choice',
        'choice_car',
        'choice_transit',
        'choice_active',
        'rt_ms',
        # Joined demographics
        'age',
        'gender',
        'education',
        'occupation_csp',
        'employment_status',
        'income_bracket',
        'income_numeric',
        'household_size',
        'children_in_household',
        'residence_type',
        'usual_commute_distance',
        'car_ownership',
        'driving_license',
        'transit_pass',
        'bike_ownership',
        'commute_days_per_week',
        # Joined traits
        'risk_general',
        'risk_driving',
        'risk_switching_row',
        'patience_general',
        'patience_switching_row',
        'patience_index',
        'nep_score',
        # Post-task
        'manip_seen',
        'attention_passed',
        'tax_fairness',
        'tax_effectiveness',
        'bonus_fairness',
        'bonus_effectiveness',
        'support_transition_funds',
        'perceived_coerciveness',
        'support_carbon_tax',
        'support_mobility_bonus'
    ]

    for p in players:
        part = p.participant
        # Read joined fields from participant.vars or persona
        demo_vars = part.vars.get('demographics', {})
        trait_vars = part.vars.get('traits', {})
        post_vars = part.vars.get('post_task', {})

        scen_id = p.scenario_id or 1
        scenario = dgp.SCENARIOS[scen_id - 1]
        treatment = p.treatment or part.treatment
        costs = dgp.get_scenario_costs(scenario, treatment)

        yield [
            p.session.code,
            part.code,
            1 if (getattr(part, 'is_bot', False) or getattr(part, '_is_bot', False)) else 0,
            treatment,
            p.round_number,
            scen_id,
            scenario['distance_km'],
            scenario['weather'],
            scenario['car_fuel_cost'],
            scenario['car_parking_cost'],
            costs['car_surcharge'],
            costs['shown_car_total'],
            scenario['transit_fare'],
            costs['transit_voucher'],
            costs['shown_transit_total'],
            costs['net_transit_advantage'],
            scenario['car_time_min'],
            scenario['transit_time_min'],
            1 if scenario['active_available'] else 0,
            scenario['active_time_min'],
            p.choice,
            p.choice_car,
            p.choice_transit,
            p.choice_active,
            p.rt_ms,
            demo_vars.get('age', ''),
            demo_vars.get('gender', ''),
            demo_vars.get('education', ''),
            demo_vars.get('occupation_csp', ''),
            demo_vars.get('employment_status', ''),
            demo_vars.get('income_bracket', ''),
            demo_vars.get('income_numeric', ''),
            demo_vars.get('household_size', ''),
            demo_vars.get('children_in_household', ''),
            demo_vars.get('residence_type', ''),
            demo_vars.get('usual_commute_distance', ''),
            demo_vars.get('car_ownership', ''),
            demo_vars.get('driving_license', ''),
            demo_vars.get('transit_pass', ''),
            demo_vars.get('bike_ownership', ''),
            demo_vars.get('commute_days_per_week', ''),
            trait_vars.get('risk_general', ''),
            trait_vars.get('risk_driving', ''),
            trait_vars.get('risk_switching_row', ''),
            trait_vars.get('patience_general', ''),
            trait_vars.get('patience_switching_row', ''),
            trait_vars.get('patience_index', ''),
            trait_vars.get('nep_score', ''),
            post_vars.get('manip_seen', ''),
            post_vars.get('attention_passed', ''),
            post_vars.get('tax_fairness', ''),
            post_vars.get('tax_effectiveness', ''),
            post_vars.get('bonus_fairness', ''),
            post_vars.get('bonus_effectiveness', ''),
            post_vars.get('support_transition_funds', ''),
            post_vars.get('perceived_coerciveness', ''),
            post_vars.get('support_carbon_tax', ''),
            post_vars.get('support_mobility_bonus', '')
        ]

