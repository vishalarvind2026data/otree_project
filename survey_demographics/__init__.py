from otree.api import *
import dgp

doc = """
Demographics Survey: Comprehensive socio-economic, spatial, and vehicle-ownership indicators.
"""


class C(BaseConstants):
    NAME_IN_URL = 'demographics'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    age = models.IntegerField(
        label="What is your age?",
        min=18,
        max=99
    )
    gender = models.StringField(
        label="What is your gender?",
        choices=[
            "Female",
            "Male",
            "Non-binary",
            "Prefer to self-describe",
            "Prefer not to say"
        ],
        widget=widgets.RadioSelect
    )
    education = models.StringField(
        label="What is your highest completed level of education?",
        choices=[
            "Secondary",
            "Vocational",
            "Bachelor",
            "Master",
            "Doctorate",
            "Other"
        ],
        widget=widgets.RadioSelect
    )
    occupation_csp = models.StringField(
        label="Which socio-professional category best describes your primary occupation?",
        choices=[
            "Executives & higher intellectual professions",
            "Intermediate professions",
            "Employees",
            "Workers",
            "Craftspeople / Shopkeepers / Business owners",
            "Farmers",
            "Students",
            "Retired",
            "Unemployed / Looking for work",
            "Other"
        ],
        widget=widgets.RadioSelect
    )
    employment_status = models.StringField(
        label="What is your current employment status?",
        choices=[
            "Full-time",
            "Part-time",
            "Self-employed",
            "Student",
            "Not employed",
            "Retired"
        ],
        widget=widgets.RadioSelect
    )
    income_bracket = models.StringField(
        label="What is your household's total net monthly income bracket (all sources combined)?",
        choices=[
            "< €1,500",
            "€1,500–€2,499",
            "€2,500–€3,499",
            "€3,500–€4,999",
            "€5,000–€6,999",
            "≥ €7,000",
            "Prefer not to say"
        ],
        widget=widgets.RadioSelect
    )
    household_size = models.IntegerField(
        label="How many people live in your household (including yourself)?",
        min=1,
        max=12
    )
    children_in_household = models.IntegerField(
        label="How many dependent children (under 18) live in your household?",
        min=0,
        max=10
    )
    residence_type = models.StringField(
        label="Which area best describes your place of residence?",
        choices=[
            "City center",
            "Inner suburb (< 10 km)",
            "Outer suburb (10–25 km)",
            "Rural / Exurban (> 25 km)"
        ],
        widget=widgets.RadioSelect
    )
    usual_commute_distance_km = models.FloatField(
        label="What is your typical one-way commute distance to work or study (in km)?",
        min=0.0,
        max=200.0
    )
    usual_commute_mode = models.StringField(
        label="What is your primary mode of transport for your regular commute?",
        choices=[
            "Private car (alone)",
            "Carpool",
            "Public transit (metro/bus/train)",
            "Bicycle / E-bike",
            "Walking",
            "Other"
        ],
        widget=widgets.RadioSelect
    )
    car_ownership = models.StringField(
        label="Do you or does your household own or lease a passenger car?",
        choices=[
            "Yes, personal car",
            "Yes, shared household car",
            "No car"
        ],
        widget=widgets.RadioSelect
    )
    driving_license = models.StringField(
        label="Do you hold a valid driving licence?",
        choices=["Yes", "No"],
        widget=widgets.RadioSelect
    )
    transit_pass_ownership = models.StringField(
        label="Do you currently hold an active public transit pass / subscription?",
        choices=["Yes", "No"],
        widget=widgets.RadioSelect
    )
    bike_ownership = models.StringField(
        label="Do you own or have regular access to a working bicycle or e-bike?",
        choices=["Yes", "No"],
        widget=widgets.RadioSelect
    )
    commute_days_per_week = models.IntegerField(
        label="How many days per week do you typically commute to your workplace or campus?",
        min=1,
        max=7
    )


class Demographics(Page):
    form_model = 'player'
    form_fields = [
        'age',
        'gender',
        'education',
        'occupation_csp',
        'employment_status',
        'income_bracket',
        'household_size',
        'children_in_household',
        'residence_type',
        'usual_commute_distance_km',
        'usual_commute_mode',
        'car_ownership',
        'driving_license',
        'transit_pass_ownership',
        'bike_ownership',
        'commute_days_per_week'
    ]

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        # Convert income bracket to numeric midpoint
        bracket_map = {
            "< €1,500": 1000,
            "€1,500–€2,499": 2000,
            "€2,500–€3,499": 3000,
            "€3,500–€4,999": 4250,
            "€5,000–€6,999": 6000,
            "≥ €7,000": 8500,
            "Prefer not to say": 3500
        }
        owns_car_num = 1 if player.car_ownership in ["Yes, personal car", "Yes, shared household car"] else 0

        player.participant.vars['demographics'] = {
            'age': player.age,
            'gender': player.gender,
            'education': player.education,
            'occupation_csp': player.occupation_csp,
            'employment_status': player.employment_status,
            'income_bracket': player.income_bracket,
            'income_numeric': bracket_map.get(player.income_bracket, 3500),
            'household_size': player.household_size,
            'children_in_household': player.children_in_household,
            'residence_type': player.residence_type,
            'usual_commute_distance': player.usual_commute_distance_km,
            'car_ownership': owns_car_num,
            'driving_license': 1 if player.driving_license == "Yes" else 0,
            'transit_pass': 1 if player.transit_pass_ownership == "Yes" else 0,
            'bike_ownership': 1 if player.bike_ownership == "Yes" else 0,
            'commute_days_per_week': player.commute_days_per_week
        }


page_sequence = [Demographics]
