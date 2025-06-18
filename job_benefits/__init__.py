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
        """
        This method runs at the start of each round. The corrected logic ensures
        that the treatment order is created for a participant if it doesn't exist,
        and then assigns the current round's treatment from that order.
        This robustly handles all rounds and players joining mid-session.
        """
        for p in self.get_players():
            # Step 1: Check if the treatment order has been created for this participant.
            # If not, create and shuffle it for them. This will run in Round 1
            # for all players, and also for any player joining a session late.
            if 'treatment_order' not in p.participant.vars:
                treatments = list(Constants.TREATMENTS)
                random.shuffle(treatments)
                p.participant.vars['treatment_order'] = treatments
            
            # Step 2: Now that we have guaranteed 'treatment_order' exists, we can
            # safely retrieve the order and assign the treatment for the current round.
            # The round_number is 1-based, list index is 0-based, so we subtract 1.
            treatment_order = p.participant.vars['treatment_order']
            p.treatment = treatment_order[self.round_number - 1]

            


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    # Field for original treatments
    accept_offer = models.BooleanField(label="Do you accept this job offer?", blank=True)
    perk_offered = models.StringField(blank=True)

    # --- REMOVED: This field is no longer needed as BonusChoice page is removed ---
    # choice_bonus = models.StringField(...)

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

    # --- NEW FIELDS for the refactored 'Choice' treatment ---
    gym_choice = models.StringField(
        label="Your choice for the Gym Membership offer:",
        choices=[['Cash', 'Accept Cash Offer'], ['Benefit', 'Accept Gym Membership'], ['Reject', 'Reject Offer']],
        widget=widgets.RadioSelect,
        blank=True
    )
    bike_choice = models.StringField(
        label="Your choice for the Work Bike offer:",
        choices=[['Cash', 'Accept Cash Offer'], ['Benefit', 'Accept Work Bike'], ['Reject', 'Reject Offer']],
        widget=widgets.RadioSelect,
        blank=True
    )

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

    def get_form_fields(self):
        if 'treatment_order' not in self.participant.vars:
            treatments = list(Constants.TREATMENTS)
            random.shuffle(treatments)
            self.participant.vars['treatment_order'] = treatments
        # Dynamically set form fields based on the treatment for the current round
        treatment = self.participant.vars['treatment_order'][self.round_number - 1]
        if treatment == 'Choice':
            return ['gym_choice', 'bike_choice']
        else:
            return ['accept_offer']

    def vars_for_template(self):
        treatment = self.participant.vars['treatment_order'][self.round_number - 1]
        self.treatment = treatment  # Store treatment for the record

        bonus_desc = ""
        adjusted_salary = Constants.BASE_SALARY  # Default salary
        player_in_round_1 = self.in_round(1)

        if treatment == 'Cash Bonus':
            bonus_desc = f"Cash bonus of €{Constants.CASH_BONUS}"
        elif treatment == 'Non-Monetary Perk':
            perk = random.choice(Constants.NON_MONETARY_PERKS)
            self.perk_offered = perk
            if perk == 'Gym Membership':
                adjusted_salary -= self.in_round(1).willingness_to_pay_gym
            elif perk == 'Work Bike':
                adjusted_salary -= self.in_round(1).willingness_to_pay_bike
            bonus_desc = f"Non-monetary perk: {perk}"
        elif treatment == 'Choice':
            # No bonus_desc needed as the choices are detailed in the template
            pass

        return dict(
            base_salary=adjusted_salary,
            treatment=treatment,
            bonus_desc=bonus_desc,
            # Pass WTP values for the 'Choice' treatment template
            wtp_gym=player_in_round_1.willingness_to_pay_gym,
            wtp_bike=player_in_round_1.willingness_to_pay_bike,
            # For robustness in template
            Constants=Constants
        )

# --- The BonusChoice page is no longer needed and should be removed ---

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
            accepted_info = "No" # Default

            if p.treatment == 'Choice':
                # For choice, we summarize the two decisions
                gym = p.gym_choice or "No decision"
                bike = p.bike_choice or "No decision"
                bonus_info = f"Gym: {gym}, Bike: {bike}"
                # Consider it "accepted" if at least one benefit/cash was chosen
                if p.gym_choice != 'Reject' or p.bike_choice != 'Reject':
                     accepted_info = "Yes (at least one)"

            elif p.treatment == 'Non-Monetary Perk':
                bonus_info = p.perk_offered
                if p.accept_offer:
                    accepted_info = "Yes"
            
            elif p.treatment == 'Cash Bonus':
                bonus_info = f"€{Constants.CASH_BONUS}"
                if p.accept_offer:
                    accepted_info = "Yes"


            accepted_treatments.append({
                'round_number': p.round_number,
                'treatment': p.treatment,
                'accepted': accepted_info,
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
            modal_time_log=self.modal_time_log,  
            # Pass the willingness to pay values from the player object of Round 1
            willingness_to_pay_gym=player_round_1.willingness_to_pay_gym,
            willingness_to_pay_bike=player_round_1.willingness_to_pay_bike,
        )


# --- UPDATED page_sequence: BonusChoice is removed ---
page_sequence = [Introduction, ValuePerception, JobOffer, JobSelection, ResultsSummary]