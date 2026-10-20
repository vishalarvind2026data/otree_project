import random
from otree.api import *
import dgp

doc = """
Survey of Behavioral and Psychological Traits:
1. Risk preferences (Dohmen general, driving-specific, lottery choice list)
2. Time preferences (Falk patience, intertemporal choice list, patience_index)
3. Environmental worldview: 15-item Revised NEP scale (Dunlap et al., 2000) with reverse coding
"""


NEP_ITEMS = [
    (1, "We are approaching the limit of the number of people the earth can support.", False),
    (2, "Humans have the right to modify the natural environment to suit their needs.", True),
    (3, "When humans interfere with nature it often produces disastrous consequences.", False),
    (4, "Human ingenuity will ensure that we do NOT make the earth unliveable.", True),
    (5, "Humans are severely abusing the environment.", False),
    (6, "The earth has plenty of natural resources if we just learn how to develop them.", True),
    (7, "Plants and animals have as much right as humans to exist.", False),
    (8, "The balance of nature is strong enough to cope with the impacts of modern industrial nations.", True),
    (9, "Despite our special abilities, humans are still subject to the laws of nature.", False),
    (10, "The so-called 'ecological crisis' facing humankind has been greatly exaggerated.", True),
    (11, "The earth is like a spaceship with very limited room and resources.", False),
    (12, "Humans were meant to rule over the rest of nature.", True),
    (13, "The balance of nature is very delicate and easily upset.", False),
    (14, "Humans will eventually learn enough about how nature works to be able to control it.", True),
    (15, "If things continue on their present course, we will soon experience a major ecological catastrophe.", False)
]


class C(BaseConstants):
    NAME_IN_URL = 'traits'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1
    NEP_ITEMS = NEP_ITEMS


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    # Risk
    risk_general = models.IntegerField(
        label="In general, how willing are you to take risks? (0 = Not at all willing, 10 = Very willing)",
        min=0,
        max=10
    )
    risk_driving = models.IntegerField(
        label="When driving or travelling on the road, how prepared are you to take risks? (0 = Completely unwilling, 10 = Fully prepared)",
        min=0,
        max=10
    )
    risk_switching_row = models.IntegerField(
        label="Lottery choice list decision: At which row (from 1 to 7) do you switch from the Safe payment to the Risky lottery (50% €50 / 50% €0)? (Enter 7 if you never switch)",
        min=1,
        max=7
    )

    # Time / Patience
    patience_general = models.IntegerField(
        label="How willing are you to give up something beneficial today in order to benefit more from it in the future? (0 = Completely unwilling, 10 = Very willing)",
        min=0,
        max=10
    )
    patience_switching_row = models.IntegerField(
        label="Intertemporal choice list: At which row (from 1 to 7) do you switch from receiving €100 today to receiving the larger amount in 1 month? (Enter 7 if you always prefer today)",
        min=1,
        max=7
    )
    patience_index = models.FloatField(initial=0.0)

    # Revised NEP Scale: 15 items (1 to 5)
    nep_1 = models.IntegerField(min=1, max=5)
    nep_2 = models.IntegerField(min=1, max=5)
    nep_3 = models.IntegerField(min=1, max=5)
    nep_4 = models.IntegerField(min=1, max=5)
    nep_5 = models.IntegerField(min=1, max=5)
    nep_6 = models.IntegerField(min=1, max=5)
    nep_7 = models.IntegerField(min=1, max=5)
    nep_8 = models.IntegerField(min=1, max=5)
    nep_9 = models.IntegerField(min=1, max=5)
    nep_10 = models.IntegerField(min=1, max=5)
    nep_11 = models.IntegerField(min=1, max=5)
    nep_12 = models.IntegerField(min=1, max=5)
    nep_13 = models.IntegerField(min=1, max=5)
    nep_14 = models.IntegerField(min=1, max=5)
    nep_15 = models.IntegerField(min=1, max=5)
    nep_item_order = models.StringField(initial="")
    nep_score = models.FloatField(initial=0.0)


class SurveyTraits(Page):
    form_model = 'player'
    form_fields = [
        'risk_general',
        'risk_driving',
        'risk_switching_row',
        'patience_general',
        'patience_switching_row',
        'nep_1', 'nep_2', 'nep_3', 'nep_4', 'nep_5',
        'nep_6', 'nep_7', 'nep_8', 'nep_9', 'nep_10',
        'nep_11', 'nep_12', 'nep_13', 'nep_14', 'nep_15'
    ]

    @staticmethod
    def vars_for_template(player: Player):
        # Deterministic or session-consistent shuffle for NEP items
        items = NEP_ITEMS.copy()
        rng = random.Random(player.participant.id_in_session * 313 + 7)
        rng.shuffle(items)
        order_str = ",".join(str(it[0]) for it in items)
        player.nep_item_order = order_str
        return {
            'shuffled_nep': items
        }

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        # 1. Compute Patience Index (scale 0 to 1)
        # Higher Falk general score & earlier switching row => higher patience
        p_row_norm = (7.0 - player.patience_switching_row) / 6.0
        p_gen_norm = player.patience_general / 10.0
        player.patience_index = round((p_gen_norm + p_row_norm) / 2.0, 3)

        # 2. Compute Revised NEP Score (scale 1.0 to 5.0)
        # Even numbered items (2, 4, 6, 8, 10, 12, 14) are reverse coded: score = 6 - val
        scored_items = []
        for i in range(1, 16):
            val = getattr(player, f'nep_{i}')
            if i % 2 == 0:
                scored = 6 - val
            else:
                scored = val
            scored_items.append(scored)

        player.nep_score = round(sum(scored_items) / 15.0, 3)

        # Save into participant.vars for custom export
        player.participant.vars['traits'] = {
            'risk_general': player.risk_general,
            'risk_driving': player.risk_driving,
            'risk_switching_row': player.risk_switching_row,
            'patience_general': player.patience_general,
            'patience_switching_row': player.patience_switching_row,
            'patience_index': player.patience_index,
            'nep_score': player.nep_score
        }


page_sequence = [SurveyTraits]
