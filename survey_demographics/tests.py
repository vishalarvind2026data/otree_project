from otree.api import Bot, Submission
from . import Demographics
import dgp

class PlayerBot(Bot):
    def play_round(self):
        participant = self.participant
        if not participant.vars.get('persona'):
            participant.vars['persona'] = dgp.generate_bot_persona(participant.id_in_session)
        p = participant.vars['persona']

        # Map binary flags to choices
        car_choice = "Yes, personal car" if p['car_ownership'] == 1 else "No car"
        license_choice = "Yes" if p['driving_license'] == 1 else "No"
        transit_choice = "Yes" if p['transit_pass'] == 1 else "No"
        bike_choice = "Yes" if p['bike_ownership'] == 1 else "No"

        yield Submission(Demographics, dict(
            age=p['age'],
            gender=p['gender'],
            education=p['education'],
            occupation_csp=p['occupation_csp'],
            employment_status=p['employment_status'],
            income_bracket=p['income_bracket'],
            household_size=p['household_size'],
            children_in_household=p['children_in_household'],
            residence_type=p['residence_type'],
            usual_commute_distance_km=p['usual_commute_distance'],
            usual_commute_mode="Private car (alone)" if p['car_ownership'] == 1 else "Public transit (metro/bus/train)",
            car_ownership=car_choice,
            driving_license=license_choice,
            transit_pass_ownership=transit_choice,
            bike_ownership=bike_choice,
            commute_days_per_week=p['commute_days_per_week']
        ))
