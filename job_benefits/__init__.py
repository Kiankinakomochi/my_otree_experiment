from otree.api import *

# Define Constants, Subsession, Group, Player first
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
            # Check if 'treatment_order' exists in participant.vars to avoid overwriting
            # if session is reloaded or if the participant object persists across apps.
            # This ensures the order is set only once per participant per session.
            if 'treatment_order' not in p.participant.vars:
                import random
                treatments = list(Constants.TREATMENTS) # Make a mutable copy
                random.shuffle(treatments) # Shuffle treatments for random order
                p.participant.vars['treatment_order'] = treatments
            p.treatment = p.participant.vars['treatment_order'][self.round_number - 1]


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    accept_offer = models.BooleanField(label="Do you accept this job offer?")
    perk_offered = models.StringField(blank=True) # Storing the specific perk offered
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
    treatment = models.StringField() # This must be defined here as it's used in Subsession.creating_session


doc = """
Your app description
"""

# PAGES
class Introduction(Page):
    def is_displayed(self):
        return self.round_number == 1

    def vars_for_template(self):
        return dict(
            instructions="You will be presented with different job offers. For each, you will decide whether to accept or reject. At the end, you will choose your preferred job from a list."
        )

class JobOffer(Page):
    form_model = 'player'
    form_fields = ['accept_offer']

    def vars_for_template(self):
        self.treatment = ""
        treatment = self.treatment
        base = Constants.BASE_SALARY
        cash = Constants.CASH_BONUS
        perks = Constants.NON_MONETARY_PERKS

        bonus_desc = "" # Initialize bonus_desc

        if treatment == 'Cash Bonus':
            bonus_desc = f"Cash bonus of €{cash}"
        elif treatment == 'Non-Monetary Perk':
            import random
            perk = random.choice(perks)
            self.perk_offered = perk  # Store the specific perk offered on the player object
            bonus_desc = f"Non-monetary perk: {perk}"
        elif treatment == 'Choice':  # It's 'Choice', not 'choice' (case sensitive)
            bonus_desc = f"You can choose either a cash bonus of €{cash} or a non-monetary perk (Gym Membership or Work Bike)."
        else: # Handle unexpected treatment values
            bonus_desc = "No specific bonus offered for this treatment type."

        return dict(
            base_salary=base,
            treatment=treatment,
            bonus_desc=bonus_desc,
        )

    def before_next_page(self, timeout_happened): 
        if self.treatment == 'Choice' and self.accept_offer:
            self._redirect_to_sibling_page('BonusChoice')

class BonusChoice(Page):
    form_model = 'player'
    form_fields = ['choice_bonus']

    def is_displayed(self):
        return self.treatment == 'Choice' and self.accept_offer


class JobTiles(Page):
    form_model = 'player'
    form_fields = ['chosen_job_tile']

    def is_displayed(self):
        return self.round_number == Constants.num_rounds

    def vars_for_template(self):
        # Prepare the list with indices directly in Python
        jobs_with_indices = []
        for i, job in enumerate(Constants.JOB_TILES):
            jobs_with_indices.append({'index': i, 'data': job})
        
        return dict(
            job_tiles=Constants.JOB_TILES, # You can keep this if needed elsewhere
            jobs_with_indices=jobs_with_indices # Pass the enumerated list
        )


class ResultsSummary(Page):
    def is_displayed(self):
        # Constants.num_rounds, not Constants.NUM_ROUNDS
        return self.round_number == Constants.num_rounds

    def vars_for_template(self):
        accepted_treatments = []
        for r in range(1, Constants.num_rounds + 1): # Constants.num_rounds
            player = self.in_round(r)
            accepted_treatments.append({
                'treatment': player.treatment,
                'accepted': player.accept_offer,
                'chosen_bonus': player.choice_bonus if hasattr(player, 'choice_bonus') else None,
                'perk_offered': player.perk_offered if hasattr(player, 'perk_offered') else None, # Include perk_offered
            })
        chosen_job = None
        if self.chosen_job_tile is not None:
            chosen_job = Constants.JOB_TILES[self.chosen_job_tile]
        return dict(
            accepted_treatments=accepted_treatments,
            chosen_job=chosen_job,
        )

page_sequence = [Introduction, JobOffer, BonusChoice, JobTiles, ResultsSummary]