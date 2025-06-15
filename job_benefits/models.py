from otree.api import *

class Constants(BaseConstants):
    name_in_url = 'job_benefits'
    players_per_group = None
    num_rounds = 3  # Three rounds

    TREATMENTS = ['Cash Bonus', 'Non-Monetary Perk', 'Choice']

    BASE_SALARY = 3000
    CASH_BONUS = 500
    NON_MONETARY_PERKS = ['Gym Membership', 'Work Bike']

    JOB_TILES = [
        dict(title='Analyst', wage=3200, benefits=['Gym Membership', 'Flexible hours']),
        dict(title='Developer', wage=3300, benefits=['Work Bike', 'Extra vacation days']),
        dict(title='Consultant', wage=3100, benefits=['Public transport ticket', 'Training courses']),
        dict(title='Manager', wage=3500, benefits=['Childcare support', 'Health program']),
    ]


class Subsession(BaseSubsession):
    def creating_session(self):
        for p in self.get_players():
            if 'treatment_order' not in p.participant.vars:
                p.participant.vars['treatment_order'] = Constants.TREATMENTS
            p.treatment = p.participant.vars['treatment_order'][self.round_number - 1]


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    treatment = models.StringField()
    accept_offer = models.BooleanField(label="Do you accept this job offer?")
    choice_bonus = models.StringField(
        choices=['Cash Bonus', 'Gym Membership', 'Work Bike'],
        widget=widgets.RadioSelect,
        blank=True,
        label="If you chose the Choice treatment, select your preferred bonus"
    )
    chosen_job_tile = models.IntegerField(
        choices=[(i, f"{job['title']} - €{job['wage']} + {', '.join(job['benefits'])}") for i, job in enumerate(Constants.JOB_TILES)],
        widget=widgets.RadioSelect,
        label="Choose your preferred job from below",
        blank=True,
    )
