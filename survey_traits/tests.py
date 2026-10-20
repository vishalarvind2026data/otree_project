from otree.api import Bot, Submission
from . import SurveyTraits
import dgp

class PlayerBot(Bot):
    def play_round(self):
        participant = self.participant
        if not participant.vars.get('persona'):
            participant.vars['persona'] = dgp.generate_bot_persona(participant.id_in_session)
        p = participant.vars['persona']

        # Build form submission dictionary
        form_dict = {
            'risk_general': p['risk_general'],
            'risk_driving': p['risk_driving'],
            'risk_switching_row': p['risk_switching_row'],
            'patience_general': p['patience_general'],
            'patience_switching_row': p['patience_switching_row']
        }

        # Add 15 NEP responses
        for i in range(1, 16):
            form_dict[f'nep_{i}'] = p['nep_responses'][f'nep_{i}']

        yield Submission(SurveyTraits, form_dict)
