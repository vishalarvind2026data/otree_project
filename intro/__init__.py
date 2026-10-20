import random
from otree.api import *
import dgp

doc = """
Introduction app: Study consent, neutral instructions, comprehension check,
and session-level randomized treatment assignment.
"""


class C(BaseConstants):
    NAME_IN_URL = 'intro'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1


class Subsession(BaseSubsession):
    pass


def creating_session(subsession: Subsession):
    session = subsession.session
    assignment_rule = session.config.get('treatment_assignment', 'balanced_random')
    fixed_treatment = session.config.get('fixed_treatment', 'A')

    players = subsession.get_players()
    n_players = len(players)

    if assignment_rule == 'fixed':
        treatments = [fixed_treatment] * n_players
    elif assignment_rule == 'simple_random':
        treatments = [random.choice(['A', 'B', 'C']) for _ in range(n_players)]
    else:  # balanced_random
        pool = ['A', 'B', 'C']
        full_cycles = n_players // 3
        remainder = n_players % 3
        t_list = pool * full_cycles
        if remainder > 0:
            extra = pool.copy()
            random.shuffle(extra)
            t_list.extend(extra[:remainder])
        random.shuffle(t_list)
        treatments = t_list

    for idx, player in enumerate(players):
        # Assign participant-level fields
        player.participant.treatment = treatments[idx]
        scenario_ids = list(range(1, 9))
        random.shuffle(scenario_ids)
        player.participant.scenario_order = scenario_ids
        # Record bot flag if initialized by otree test or simulator
        is_bot = getattr(player.participant, '_is_bot', False)
        player.participant.is_bot = bool(is_bot)
        player.participant.persona = None


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    consent_given = models.BooleanField(
        label="I have read the information above and freely agree to participate in this study.",
        widget=widgets.CheckboxInput,
        initial=False
    )
    comp_q1 = models.IntegerField(
        label="Are the commuting options presented in terms of estimated monthly costs and travel times?",
        choices=[
            [1, "Yes, monthly totals with estimated daily per-trip equivalents"],
            [2, "No, annual costs only"]
        ],
        widget=widgets.RadioSelect
    )
    comp_q2 = models.IntegerField(
        label="How many distinct commuting scenarios will you evaluate in the choice task?",
        choices=[
            [1, "4 scenarios"],
            [2, "8 scenarios"],
            [3, "16 scenarios"]
        ],
        widget=widgets.RadioSelect
    )


class Consent(Page):
    form_model = 'player'
    form_fields = ['consent_given']

    @staticmethod
    def error_message(player: Player, values):
        if not values.get('consent_given'):
            return "You must provide consent to participate in this study."


class Instructions(Page):
    @staticmethod
    def vars_for_template(player: Player):
        return {
            'treatment': player.participant.treatment
        }


class ComprehensionCheck(Page):
    form_model = 'player'
    form_fields = ['comp_q1', 'comp_q2']


page_sequence = [Consent, Instructions, ComprehensionCheck]
