import logging
from otree.api import *
import random
import json

# =============================================================================
# 1. MODELS
# =============================================================================

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
    # --- Fields for ValuePerception page (Round 1) ---
    willingness_to_pay_gym = models.CurrencyField(
        label="What is the maximum amount you would be willing to pay per year for a premium gym membership (access to all facilities, classes, etc.)?",
        blank=True,
        min=0,
        max=10000,
    )
    willingness_to_pay_bike = models.CurrencyField(
        label="What is the maximum amount you would be willing to pay per year for a work bicycle (including maintenance and insurance)?",
        blank=True, min=0, max=10000
    )

    # --- Fields for NEW JobPreference page (Round 1) ---
    chosen_job_tile = models.IntegerField(
        label="Please choose your preferred job title from the list below.",
        blank=True
    )
    preferred_salary = models.CurrencyField(
        label="What is your preferred yearly salary for this position?",
        blank=True,
        min=0
    )

    # --- Fields for JobOffer page (All Rounds) ---
    treatment = models.StringField()
    accept_offer = models.BooleanField(label="Do you accept this job offer?", blank=True)
    perk_offered = models.StringField(blank=True)
    gym_choice = models.StringField(
        choices=[['Cash', 'Accept Cash Offer'], ['Benefit', 'Accept Gym Membership'], ['Reject', 'Reject Offer']],
        widget=widgets.RadioSelect,
        blank=True
    )
    bike_choice = models.StringField(
        choices=[['Cash', 'Accept Cash Offer'], ['Benefit', 'Accept Work Bike'], ['Reject', 'Reject Offer']],
        widget=widgets.RadioSelect,
        blank=True
    )
    
    # This field now stores the index of the chosen package from Constants.JOB_TILES
    chosen_job_package_index = models.IntegerField(
        label="Please choose your preferred job package.",
        blank=True
    )
    modal_time_log = models.StringField(blank=True)


# =============================================================================
# 2. PAGES
# =============================================================================

class Introduction(Page):
    def is_displayed(self):
        return self.round_number == 1

class ValuePerception(Page):
    form_model = 'player'
    form_fields = ['willingness_to_pay_gym', 'willingness_to_pay_bike']

    def is_displayed(self):
        # This ensures the page is only shown in the first round.
        return self.round_number == 1

# --- NEW PAGE ---
class JobPreference(Page):
    """
    New page where participants select their preferred job title and salary.
    This page is displayed only in the first round.
    """
    form_model = 'player'
    form_fields = ['chosen_job_tile', 'preferred_salary']

    def is_displayed(self):
        return self.round_number == 1
    
    def vars_for_template(self):
        return dict(
            job_tiles=Constants.JOB_TILES
        )

class JobOffer(Page):
    form_model = 'player'

    def get_form_fields(self):
        # Ensure treatment order exists
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
        player_in_round_1 = self.in_round(1)
        adjusted_salary = player_in_round_1.preferred_salary or Constants.BASE_SALARY

        # Get the job title chosen in round 1
        chosen_job_index = player_in_round_1.field_maybe_none('chosen_job_tile')
        job_title = "General Position" # Default title
        if chosen_job_index is not None:
            job_title = Constants.JOB_TILES[chosen_job_index]['title']

        if treatment == 'Cash Bonus':
            bonus_desc = f"Cash bonus of €{Constants.CASH_BONUS}"
        elif treatment == 'Non-Monetary Perk':
            perk = random.choice(Constants.NON_MONETARY_PERKS)
            self.perk_offered = perk
            # The salary adjustment logic remains as it was
            if perk == 'Gym Membership':
                adjusted_salary -= player_in_round_1.willingness_to_pay_gym
            elif perk == 'Work Bike':
                adjusted_salary -= player_in_round_1.willingness_to_pay_bike
            bonus_desc = f"Non-monetary perk: {perk}"
        return dict(
            job_title=job_title,
            base_salary=adjusted_salary,
            treatment=treatment,
            bonus_desc=bonus_desc,
            wtp_gym=player_in_round_1.willingness_to_pay_gym,
            wtp_bike=player_in_round_1.willingness_to_pay_bike,
            Constants=Constants
        )

class JobSelection(Page):
    form_model = 'player'
    # The form field is updated to match the new Player model field
    form_fields = ['chosen_job_package_index', 'modal_time_log']

    def is_displayed(self):
        # Only display this page in the final round
        return self.round_number == Constants.num_rounds

    def vars_for_template(self):
        player_in_round_1 = self.in_round(1)
        player_in_final_round = self.in_round(Constants.num_rounds)

        time_log_data = player_in_final_round.field_maybe_none('modal_time_log')
        final_package_index = player_in_final_round.field_maybe_none('chosen_job_package_index')
        # Get the index of the job title chosen on the JobPreference page
        preferred_job_index = player_in_round_1.field_maybe_none('chosen_job_tile')

        
        
        chosen_title = "General Position"
        if preferred_job_index is not None:
            chosen_title = Constants.JOB_TILES[preferred_job_index]['title']
        
        # 1. Create packages for display with the consistent title
        job_packages_for_display = []
        for i, original_job in enumerate(Constants.JOB_TILES):
            job_packages_for_display.append({
                'title': chosen_title,  # Use the title the participant chose
                'wage': original_job['wage'],
                'benefits_summary': [b for b in original_job.get('benefits', [])],
                'index': i
            })
            
        return dict(
            # Data for displaying the tiles
            job_packages_for_display=job_packages_for_display,
            modal_time_log = self.field_maybe_none('modal_time_log'),
            # Complete, raw data for the JavaScript modal
            job_tiles_for_script=Constants.JOB_TILES,
        )

class ResultsSummary(Page):
    def is_displayed(self):
        return self.round_number == Constants.num_rounds

    def vars_for_template(self):
        player_in_round_1 = self.in_round(1)
        player_in_final_round = self.in_round(Constants.num_rounds)

        accepted_treatments = []
        for p in self.in_all_rounds():
            bonus_info = "N/A"
            accepted_info = "No"  # Default

            if p.treatment == 'Choice':
                gym = p.gym_choice or "No decision"
                bike = p.bike_choice or "No decision"
                bonus_info = f"Gym: {gym}, Bike: {bike}"
                if p.gym_choice in ['Cash', 'Benefit'] or p.bike_choice in ['Cash', 'Benefit']:
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

        # 3. Use the local variables that safely stored your data.
        time_log_data = player_in_final_round.field_maybe_none('modal_time_log')
        final_package_index = player_in_final_round.field_maybe_none('chosen_job_package_index')
        chosen_package_info = None
        if final_package_index is not None:
            chosen_package_info = Constants.JOB_TILES[final_package_index]
        
        preferred_title = "Not chosen"
        preferred_job_index = player_in_round_1.field_maybe_none('chosen_job_tile')
        if preferred_job_index is not None:
            preferred_title = Constants.JOB_TILES[preferred_job_index]['title']

        parsed_time_log = None
        if time_log_data:
            try:
                parsed_time_log = json.loads(time_log_data)
            except json.JSONDecodeError:
                parsed_time_log = {'Error': 'Could not parse time log data.'}

        # 4. Construct the final dictionary for the template.
        return dict(
            accepted_treatments=accepted_treatments,
            chosen_package_info=chosen_package_info,
            preferred_title=preferred_title,
            parsed_time_log=parsed_time_log,
            modal_time_log=time_log_data,
            preferred_salary=player_in_round_1.preferred_salary,
            willingness_to_pay_gym=player_in_round_1.willingness_to_pay_gym,
            willingness_to_pay_bike=player_in_round_1.willingness_to_pay_bike,
        )

# =============================================================================
# 3. PAGE SEQUENCE
# =============================================================================
page_sequence = [
    Introduction,
    ValuePerception,
    JobPreference,
    JobOffer,
    JobSelection,
    ResultsSummary
]