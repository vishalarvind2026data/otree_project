from otree.api import Bot, Submission, expect
from . import ChoicePage, C
import dgp

class PlayerBot(Bot):
    def play_round(self):
        participant = self.participant
        treatment = participant.treatment

        # Initialize persona if not yet cached on participant
        if not participant.vars.get('persona'):
            participant.vars['persona'] = dgp.generate_bot_persona(participant.id_in_session)
        persona = participant.vars['persona']

        # Current scenario
        order = participant.scenario_order
        scenario_idx = order[self.round_number - 1]
        scenario = dgp.SCENARIOS[scenario_idx - 1]

        # Verify treatment-dependent DOM text presence/absence
        if treatment == 'B':
            expect("Carbon Pollution Surcharge: +€30/month", "in", self.html)
            expect("Clean Mobility Pass Voucher", "not in", self.html)
        elif treatment == 'C':
            expect("Clean Mobility Pass Voucher: −€30/month", "in", self.html)
            expect("Carbon Pollution Surcharge", "not in", self.html)
        else:  # Treatment A
            expect("Carbon Pollution Surcharge", "not in", self.html)
            expect("Clean Mobility Pass Voucher", "not in", self.html)

        # Mathematical assertion of exact net transit advantage equivalence
        costs_A = dgp.get_scenario_costs(scenario, 'A')
        costs_B = dgp.get_scenario_costs(scenario, 'B')
        costs_C = dgp.get_scenario_costs(scenario, 'C')
        expect(costs_B['net_transit_advantage'], costs_C['net_transit_advantage'])
        expect(costs_B['net_transit_advantage'], costs_A['net_transit_advantage'] + 30)

        # Simulate choice with injected treatment effects
        sim = dgp.simulate_choice(persona, scenario, treatment)

        # Submit simulated choice
        yield Submission(ChoicePage, dict(
            choice=sim['choice'],
            rt_ms=sim['rt_ms']
        ))
