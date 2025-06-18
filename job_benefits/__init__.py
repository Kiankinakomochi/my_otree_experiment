import logging
from otree.api import *
import random # Import random here as well if not already present

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
        dict(
            title='Analyst',
            wage=3200,
            benefits=['Gym Membership', 'Flexible hours'],
            description='As an Analyst, you will be responsible for collecting, interpreting, and presenting data to help the organization make informed decisions. This role requires strong analytical skills and attention to detail.',
            benefit_details={
                'Gym Membership': 'Access to a premium gym facility with classes and personal training options.',
                'Flexible hours': 'The ability to adjust your work schedule to better fit your personal needs and commitments.'
            }
        ),
        dict(
            title='Developer',
            wage=3300,
            benefits=['Work Bike', 'Extra vacation days'],
            description='As a Developer, you will design, build, and maintain software applications and systems. You will work on coding, testing, and debugging to create efficient and scalable solutions.',
            benefit_details={
                'Work Bike': 'A company-provided bicycle for commuting and personal use, including maintenance and insurance.',
                'Extra vacation days': 'Additional paid leave beyond the standard allowance to enjoy more personal time.'
            }
        ),
        dict(
            title='Consultant',
            wage=3100,
            benefits=['Public transport ticket', 'Training courses'],
            description='As a Consultant, you will provide expert advice and strategic solutions to clients across various industries. This involves identifying problems, developing recommendations, and assisting with implementation.',
            benefit_details={
                'Public transport ticket': 'A subsidized or fully covered monthly pass for public transportation.',
                'Training courses': 'Opportunities to attend professional development courses and workshops to enhance your skills.'
            }
        ),
        dict(
            title='Manager',
            wage=3500,
            benefits=['Childcare support', 'Health program'],
            description='As a Manager, you will lead a team, oversee projects, and make key strategic decisions to achieve organizational goals. This role demands strong leadership, communication, and organizational skills.',
            benefit_details={
                'Childcare support': 'Financial assistance or access to childcare facilities to support working parents.',
                'Health program': 'Comprehensive wellness programs, including health screenings, fitness challenges, and mental health resources.'
            }
        ),
    ]


class Subsession(BaseSubsession):
    def creating_session(self):
        # Initialize treatment order if not already done (for all players across all rounds)
        for p in self.get_players():
            if 'treatment_order' not in p.participant.vars:
                treatments = list(Constants.TREATMENTS)
                random.shuffle(treatments)
                p.participant.vars['treatment_order'] = treatments


        # Now we populate p.treatment from the treatment order immediately:
        for p in self.get_players():
            p.treatment = p.participant.vars['treatment_order'][p.round_number - 1]

            


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
    chosen_job_tile = models.IntegerField(blank=True)
    treatment = models.StringField()
    # --- REMOVED: This field is no longer necessary with the modal design ---
    # confirm_or_go_back = models.StringField()

    willingness_to_pay_gym = models.CurrencyField(
        label="What is the maximum amount you would be willing to pay per year for a premium gym membership (access to all facilities, classes, etc.)?",
        blank=True,
        min=0, # Participants should not be able to enter negative values
        max=10000, # Set a reasonable maximum to prevent typos (adjust as needed)
    )
    willingness_to_pay_bike = models.CurrencyField(
        label="What is the maximum amount you would be willing to pay per year for a work bicycle (including maintenance and insurance)?",
        blank=True, min=0, max=10000
    )

    # --- NEW FIELD ---
    # This field will store a JSON string of the time spent on each modal.
    # e.g., '{"Analyst": 5500, "Developer": 12345}'
    modal_time_log = models.StringField(blank=True)


# ... (Introduction, ValuePerception, JobOffer, BonusChoice Pages remain the same) ...
class Introduction(Page):
    def is_displayed(self):
        return self.round_number == 1

class ValuePerception(Page):
    form_model = 'player'
    form_fields = ['willingness_to_pay_gym', 'willingness_to_pay_bike']

    def is_displayed(self):
        # This ensures the page is only shown in the first round.
        return self.round_number == 1

class JobOffer(Page):
    form_model = 'player'
    form_fields = ['accept_offer']

    def vars_for_template(self): # <--- This line needs to be indented
        # --- FIX: Ensure treatment_order exists before accessing it ---
        if 'treatment_order' not in self.participant.vars:
            treatments = list(Constants.TREATMENTS)
            random.shuffle(treatments)
            self.participant.vars['treatment_order'] = treatments
        # STEP 1: Derive the treatment directly from the reliable source of truth.
        treatment = self.participant.vars['treatment_order'][self.round_number - 1]
        self.treatment = treatment  # Store the treatment in the player instance for later usefi

        bonus_desc = ""
        if treatment == 'Cash Bonus':
            bonus_desc = f"Cash bonus of €{Constants.CASH_BONUS}"
        elif treatment == 'Non-Monetary Perk':
            # --- FIX: Set perk_offered here for Non-Monetary Perk treatment ---
            if self.treatment == 'Non-Monetary Perk':
                self.perk_offered = random.choice(Constants.NON_MONETARY_PERKS)
            else:
                # Ensure it's explicitly set to None or empty string if not a non-monetary perk
                # This prevents it from holding a value from a previous round if a player
                # switches from 'Non-Monetary Perk' to another treatment.
                self.perk_offered = '' # Or None, depending on preference. Empty string is often safer for StringField.
            bonus_desc = f"Non-monetary perk: {self.perk_offered}"
        elif treatment == 'Choice':
            bonus_desc = f"You can choose either a cash bonus of €{Constants.CASH_BONUS} or a non-monetary perk (Gym Membership or Work Bike)."

        return dict(
            base_salary=Constants.BASE_SALARY,
            treatment=treatment,
            bonus_desc=bonus_desc,
        )
class BonusChoice(Page):
    form_model = 'player'
    form_fields = ['choice_bonus']

    def is_displayed(self):
        # This page's display logic must also use the reliable source of truth.
        treatment = self.participant.vars['treatment_order'][self.round_number - 1]
        return treatment == 'Choice' and self.field_maybe_none('accept_offer') is True

# --- REFACTORED: Merged JobTiles and JobDescriptionPage into JobSelection ---
class JobSelection(Page):
    form_model = 'player'
    # --- ADDED `modal_time_log` TO THE FORM FIELDS ---
    form_fields = ['chosen_job_tile', 'modal_time_log']

    def is_displayed(self):
        # Only display this page in the final round
        return self.round_number == Constants.num_rounds

    def vars_for_template(self):
        # Pass the job data to the template. json.dumps is not needed for this.
        return dict(
            job_tiles=Constants.JOB_TILES,
        )

class ResultsSummary(Page):
    def is_displayed(self):
        return self.round_number == Constants.num_rounds

    def vars_for_template(self):
        accepted_treatments = []
        for p in self.in_all_rounds():
            bonus_info = "N/A"
            if p.treatment == 'Choice' and p.accept_offer:
                bonus_info = p.choice_bonus
            elif p.treatment == 'Non-Monetary Perk':
                bonus_info = p.perk_offered

            accepted_treatments.append({
                'round_number': p.round_number,
                'treatment': p.treatment,
                'accepted': "Yes" if p.accept_offer else "No",
                'bonus_info': bonus_info,
            })
        
        chosen_job = None
        if self.field_maybe_none('chosen_job_tile') is not None:
            chosen_job = Constants.JOB_TILES[self.chosen_job_tile]

        # Get the player object from Round 1 to access WTP values
        # self.in_round(1) retrieves the player object for the current participant in round 1.
        player_round_1 = self.in_round(1) 
            
        return dict(
            accepted_treatments=accepted_treatments,
            chosen_job=chosen_job,
            # Pass the willingness to pay values from the player object of Round 1
            willingness_to_pay_gym=player_round_1.willingness_to_pay_gym,
            willingness_to_pay_bike=player_round_1.willingness_to_pay_bike,
        )

# --- UPDATED: page_sequence now uses the new JobSelection page ---
page_sequence = [Introduction, ValuePerception, JobOffer, BonusChoice, JobSelection, ResultsSummary]