from otree.api import Bot, Submission
from . import PostTaskSurvey, Debrief
import dgp

class PlayerBot(Bot):
    def play_round(self):
        participant = self.participant
        treatment = participant.treatment

        if not participant.vars.get('persona'):
            participant.vars['persona'] = dgp.generate_bot_persona(participant.id_in_session)
        persona = participant.vars['persona']

        # Simulate post-task responses based on attentive/inattentive status and treatment
        sim = dgp.simulate_post_task(persona, treatment)

        # Attentive bots select 1 for attention check; inattentive may fail
        att_val = 1 if sim['attention_passed'] == 1 else 3

        yield Submission(PostTaskSurvey, dict(
            manip_seen=sim['manip_seen'],
            attention_check_raw=att_val,
            tax_fairness=sim['tax_fairness'],
            tax_effectiveness=sim['tax_effectiveness'],
            bonus_fairness=sim['bonus_fairness'],
            bonus_effectiveness=sim['bonus_effectiveness'],
            support_transition_funds=sim['support_transition_funds'],
            perceived_coerciveness=sim['perceived_coerciveness'],
            support_carbon_tax=sim['support_carbon_tax'],
            support_mobility_bonus=sim['support_mobility_bonus']
        ))

        yield Submission(Debrief, dict(comments="Simulated bot session."))
