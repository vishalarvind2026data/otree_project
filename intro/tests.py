from otree.api import Bot, Submission
from . import Consent, Instructions, ComprehensionCheck

class PlayerBot(Bot):
    def play_round(self):
        yield Submission(Consent, dict(consent_given=True))
        yield Submission(Instructions)
        yield Submission(ComprehensionCheck, dict(comp_q1=1, comp_q2=2))
