from otree.api import *
import dgp

doc = """
Post-Task App: Manipulation check, attention check, policy acceptability,
perceived fairness, psychological reactance, abstract policy support, and study debriefing.
"""


class C(BaseConstants):
    NAME_IN_URL = 'post_task'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    # Manipulation check
    manip_seen = models.StringField(
        label="During the 8 commuting scenarios you completed earlier, which specific policy line item was displayed on the choice options?",
        choices=[
            "A Carbon Pollution Surcharge on the car option",
            "A Clean Mobility Pass Voucher on the public transit option",
            "No extra surcharge or voucher",
            "I do not remember"
        ],
        widget=widgets.RadioSelect
    )

    # Attention check (instructed response: select 1 / Strongly Disagree)
    attention_check_raw = models.IntegerField(
        label="Transport policy is a subject with many viewpoints. To confirm that you are reading questions attentively, please select 'Strongly disagree' (1) for this statement.",
        choices=[
            [1, "1 - Strongly Disagree"],
            [2, "2 - Disagree"],
            [3, "3 - Neutral"],
            [4, "4 - Agree"],
            [5, "5 - Strongly Agree"]
        ],
        widget=widgets.RadioSelect
    )
    attention_passed = models.IntegerField(initial=0)

    # Policy acceptability & perceived fairness (1 to 7)
    tax_fairness = models.IntegerField(
        label="In terms of fairness, how do you evaluate a carbon tax surcharge on private vehicle fossil fuel use? (1 = Very unfair to 7 = Very fair)",
        min=1,
        max=7
    )
    tax_effectiveness = models.IntegerField(
        label="How effective do you believe a carbon tax surcharge is in encouraging modal shift away from private cars? (1 = Not effective at all to 7 = Extremely effective)",
        min=1,
        max=7
    )
    bonus_fairness = models.IntegerField(
        label="In terms of fairness, how do you evaluate a publicly funded Clean Mobility Voucher subsidizing public transit? (1 = Very unfair to 7 = Very fair)",
        min=1,
        max=7
    )
    bonus_effectiveness = models.IntegerField(
        label="How effective do you believe a Clean Mobility Voucher is in encouraging commuters to use public transit? (1 = Not effective at all to 7 = Extremely effective)",
        min=1,
        max=7
    )
    support_transition_funds = models.IntegerField(
        label="How strongly do you support allocating municipal budget toward clean transport transition policies? (1 = Strongly Oppose to 7 = Strongly Support)",
        min=1,
        max=7
    )

    # Reactance / Perceived Coerciveness (1 to 7)
    perceived_coerciveness = models.IntegerField(
        label="To what extent do you feel that transport policies and surcharges restrict your individual freedom of mobility choice? (1 = Not at all coercive to 7 = Highly coercive)",
        min=1,
        max=7
    )

    # Abstract policy support (1 to 7)
    support_carbon_tax = models.IntegerField(
        label="In the abstract, how strongly do you support or oppose a carbon tax on passenger vehicle fuels? (1 = Strongly Oppose to 7 = Strongly Support)",
        min=1,
        max=7
    )
    support_mobility_bonus = models.IntegerField(
        label="In the abstract, how strongly do you support or oppose a Clean Mobility Bonus pass for public transit? (1 = Strongly Oppose to 7 = Strongly Support)",
        min=1,
        max=7
    )

    comments = models.LongStringField(
        label="Optional: Please share any comments or thoughts regarding this study or transport policies in general:",
        blank=True
    )


class PostTaskSurvey(Page):
    form_model = 'player'
    form_fields = [
        'manip_seen',
        'attention_check_raw',
        'tax_fairness',
        'tax_effectiveness',
        'bonus_fairness',
        'bonus_effectiveness',
        'support_transition_funds',
        'perceived_coerciveness',
        'support_carbon_tax',
        'support_mobility_bonus'
    ]

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        # Grade attention check
        player.attention_passed = 1 if player.attention_check_raw == 1 else 0

        # Save to participant.vars
        player.participant.vars['post_task'] = {
            'manip_seen': player.manip_seen,
            'attention_passed': player.attention_passed,
            'tax_fairness': player.tax_fairness,
            'tax_effectiveness': player.tax_effectiveness,
            'bonus_fairness': player.bonus_fairness,
            'bonus_effectiveness': player.bonus_effectiveness,
            'support_transition_funds': player.support_transition_funds,
            'perceived_coerciveness': player.perceived_coerciveness,
            'support_carbon_tax': player.support_carbon_tax,
            'support_mobility_bonus': player.support_mobility_bonus
        }


class Debrief(Page):
    form_model = 'player'
    form_fields = ['comments']

    @staticmethod
    def vars_for_template(player: Player):
        return {
            'treatment': player.participant.treatment
        }


page_sequence = [PostTaskSurvey, Debrief]
