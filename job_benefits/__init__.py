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
    CASH_BONUS = 800
    NON_MONETARY_PERKS = ['Gym Membership', 'Work Bike']

    # This list defines the benefits that will be presented to the user for ranking.
    # It's crucial that the text here exactly matches what you might use elsewhere if you're cross-referencing.
    BENEFITS_TO_RANK = [
        'Public Transport Ticket',
        'Company E-Bike',
        'Premium Gym Membership',
        'Extra Vacation Days',
        'Professional Development Budget',
        'Catered Lunch Program',
        'Home Office Setup',
        'Flexible Wellness Program',
    ]
    
    # This dictionary provides descriptions for the benefits to be ranked.
    BENEFIT_DESCRIPTIONS = {
        'Public Transport Ticket': 'A monthly pass for all local public transportation.',
        'Company E-Bike': 'Get a modern, high-quality e-bike for both your daily commute and personal use. This worry-free package includes all maintenance and insurance.',
        'Premium Gym Membership': 'Full access to a premium gym facility with classes and personal training options.',
        'Extra Vacation Days': 'Two additional days of paid leave beyond the standard allowance.',
        'Professional Development Budget': 'An annual budget to be spent on approved training courses, conferences, or books.',
        'Catered Lunch Program': 'Enjoy complimentary meals from a selection of local restaurants and delivery services several days a week.',
        'Home Office Setup': 'The company will provide you with a high-quality ergonomic chair, a large external monitor, and other accessories for a comfortable and productive home office.',
        'Flexible Wellness Program': 'Choose from a wide range of company-sponsored wellness activities that fit your lifestyle, such as yoga classes, meditation app subscriptions, or sports club fees.',
    }


    JOB_TILES = [
        dict(
            title='Analyst',
            wage=3200,
            benefits=['Gym Membership', 'Flexible hours'],
            description='As an Analyst, you will be responsible for collecting, interpreting, and presenting data to help the organization make informed decisions. This role requires strong analytical skills and attention to detail.',
            benefit_details={
                'Gym Membership': 'Access to a premium gym facility with classes and personal training options.',
                'Home Office Setup': 'The company will provide you with a high-quality ergonomic chair, and other accessories and devices (e.g. monitors) for a comfortable and productive home office.'
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
                'Catered Lunch Program': 'Enjoy complimentary meals from a selection of local restaurants and delivery services several days a week.',
                'Health program': 'Choose from a wide range of company-sponsored wellness activities that fit your lifestyle, such as yoga classes, meditation app subscriptions'
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
    # These fields now store the *monthly* willingness to pay.
    willingness_to_pay_gym = models.CurrencyField(
        label="What is the maximum amount you would be willing to pay per month for a premium gym membership (access to all facilities, classes, etc.)?",
        blank=False,
        min=0,
        max=10000 / 12, # Adjusted max to be more reasonable for monthly
    )
    willingness_to_pay_bike = models.CurrencyField(
        label="What is the maximum amount you would be willing to pay per month for a work bicycle (including maintenance and insurance)?",
        blank=False,
        min=0,
        max=10000 / 12, # Adjusted max to be more reasonable for monthly
    )

    # --- Fields for NEW JobPreference page (Round 1) ---
    chosen_job_tile = models.IntegerField(
        label="Please choose your preferred job title from the list below.",
        blank=True
    )
    preferred_salary = models.CurrencyField(
        label="What is your preferred yearly salary for this position?",
        blank=False,
        min=0
    )

    # --- NEW ---
    # Field to store the benefit ranking. It will be a comma-separated string from the JS widget.
    benefit_ranking = models.LongStringField(blank=True)

    treatment = models.StringField()
    
    # NEW fields for the 'Cash Bonus' round
    accept_cash_gym = models.BooleanField(label="Do you accept this cash offer?", blank=True)
    accept_cash_bike = models.BooleanField(label="Do you accept this cash offer?", blank=True)

    # NEW fields for the 'Non-Monetary Perk' round
    accept_perk_gym = models.BooleanField(label="Do you accept the Gym Membership offer?", blank=True)
    accept_perk_bike = models.BooleanField(label="Do you accept the Work Bike offer?", blank=True)

    # Fields for the 'Choice' round (unchanged)
    gym_choice = models.StringField(choices=[['Cash', 'Accept Cash'], ['Benefit', 'Accept Gym Membership'], ['Reject', 'Reject Offer']], widget=widgets.RadioSelect, blank=True)
    bike_choice = models.StringField(choices=[['Cash', 'Accept Cash'], ['Benefit', 'Accept Work Bike'], ['Reject', 'Reject Offer']], widget=widgets.RadioSelect, blank=True)
    
    # --- Field for Final Job Selection Task ---
    chosen_job_package_index = models.IntegerField(label="Chosen Job Package", blank=True)
    modal_time_log = models.StringField(blank=True)

    def get_dynamic_job_packages(self):
        """
        Generates the personalized list of 4 job packages based on this player's
        ranking and preferences from round 1. This function can be called from any page.
        """
        player_in_round_1 = self.in_round(1)

        # Get the participant's ranking and preferred salary from round 1
        ranked_benefits_str = player_in_round_1.field_maybe_none('benefit_ranking')
        # Use a sensible default for salary if not provided
        preferred_salary = player_in_round_1.field_maybe_none('preferred_salary') or Constants.BASE_SALARY
        
        # --- MODIFIED LOGIC ---
        # Instead of using the flawed wtp_sum, we now define the salary trade-off range
        # using the experiment's own CASH_BONUS value. This makes the trade-off
        # consistent and economically meaningful across all participants and benefits.
        max_salary_reduction = Constants.CASH_BONUS

        preferred_job_index = player_in_round_1.field_maybe_none('chosen_job_tile')
        chosen_title = "General Position"
        if preferred_job_index is not None and preferred_job_index < len(Constants.JOB_TILES):
            chosen_title = Constants.JOB_TILES[preferred_job_index]['title']
        
        job_packages = []
        
        # Fallback in case ranking data is missing
        if not ranked_benefits_str:
            # You can define a more robust fallback here if needed
            return [] 
        
        # Create the personalized tiers
        ranked_benefits = ranked_benefits_str.split(',')
        
        tier1_salary = preferred_salary
        tier4_salary = max(0, preferred_salary - max_salary_reduction)
        salary_step = (tier1_salary - tier4_salary) / 3 if max_salary_reduction > 0 else 0
        
        salaries = [
            round(tier1_salary),
            round(tier1_salary - salary_step),
            round(tier1_salary - 2 * salary_step),
            round(tier4_salary)
        ]
        
        num_ranked = len(ranked_benefits)
        if num_ranked < 4: # Add a safeguard for very short rankings
            return []

        benefit_tiers = [
            ranked_benefits[0],
            ranked_benefits[1],
            ranked_benefits[num_ranked - 3],
            ranked_benefits[num_ranked - 2],
        ]
        
        # Build the 4 personalized job tiles
        for i in range(4):
            benefit_name = benefit_tiers[3-i]
            job_packages.append({
                'title': chosen_title,
                'wage': salaries[i],
                'benefits_summary': [benefit_name], # Inversely matched
                'index': i,
                'benefit_details': {
                    benefit_name: Constants.BENEFIT_DESCRIPTIONS.get(benefit_name, '')
                }
            })
        
        return job_packages


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

# --- NEW PAGE ---
class BenefitRanking(Page):
    """
    On this page, participants rank a list of non-monetary benefits.
    The page uses a JavaScript widget (e.g., SortableJS) to allow drag-and-drop ranking.
    The order is saved into the hidden 'benefit_ranking' form field.
    """
    form_model = 'player'
    form_fields = ['benefit_ranking']

    def is_displayed(self):
        return self.round_number == 1

    def vars_for_template(self):
        """
        This method now pre-processes the data in Python to make it easier for the template.
        It combines the benefit names and descriptions into a single list of dictionaries.
        """
        benefits_data = []
        for benefit_name in Constants.BENEFITS_TO_RANK:
            benefits_data.append({
                'name': benefit_name,
                'description': Constants.BENEFIT_DESCRIPTIONS.get(benefit_name, 'Description not found.')
            })
        
        return {'benefits_data': benefits_data}


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
        elif treatment == 'Cash Bonus':
            return ['accept_cash_gym', 'accept_cash_bike']
        elif treatment == 'Non-Monetary Perk':
            return ['accept_perk_gym', 'accept_perk_bike']
        return []

    def vars_for_template(self):
        treatment = self.participant.vars['treatment_order'][self.round_number - 1]
        self.treatment = treatment  # Store treatment for the record

        bonus_desc = ""
        player_in_round_1 = self.in_round(1)
        
        # --- REVISED LOGIC ---
        # The base salary is ALWAYS the preferred salary. No more adjustments.
        base_salary = player_in_round_1.preferred_salary or Constants.BASE_SALARY

        # Get the job title chosen in round 1
        chosen_job_index = player_in_round_1.field_maybe_none('chosen_job_tile')
        job_title = "General Position"
        if chosen_job_index is not None:
            job_title = Constants.JOB_TILES[chosen_job_index]['title']
        
        # Multiply the monthly willingness to pay by 12 for yearly display
        yearly_wtp_gym = player_in_round_1.willingness_to_pay_gym * 12
        yearly_wtp_bike = player_in_round_1.willingness_to_pay_bike * 12

        return dict(
            job_title=job_title,
            base_salary=base_salary,  # Use the clean, non-adjusted salary
            treatment=self.treatment,
            wtp_gym=yearly_wtp_gym,  # Now displays the yearly amount
            wtp_bike=yearly_wtp_bike,  # Now displays the yearly amount
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
        # The complex logic is now in the Player model. We just call the function.
        job_packages_for_display = self.get_dynamic_job_packages()

        return dict(
            # Data for displaying the tiles
            job_packages_for_display=job_packages_for_display,
            modal_time_log = self.field_maybe_none('modal_time_log'),
            job_tiles_for_script=job_packages_for_display
        )

class ResultsSummary(Page):
    def is_displayed(self):
        return self.round_number == Constants.num_rounds

    def vars_for_template(self):
        player_in_round_1 = self.in_round(1)
        
        accepted_treatments = []
        for p in self.in_all_rounds():
            bonus_info = ""
            accepted_info = ""
            
            if p.treatment == 'Cash Bonus':
                gym_decision = "Accepted" if p.accept_cash_gym else "Rejected"
                bike_decision = "Accepted" if p.accept_cash_bike else "Rejected"
                bonus_info = f"Gym-Cash Offer: {gym_decision}, Bike-Cash Offer: {bike_decision}"

            elif p.treatment == 'Non-Monetary Perk':
                gym_decision = "Accepted" if p.accept_perk_gym else "Rejected"
                bike_decision = "Accepted" if p.accept_perk_bike else "Rejected"
                bonus_info = f"Gym Perk Offer: {gym_decision}, Bike Perk Offer: {bike_decision}"

            elif p.treatment == 'Choice':
                gym_decision = p.gym_choice or "No decision"
                bike_decision = p.bike_choice or "No decision"
                bonus_info = f"Gym Choice: {gym_decision}, Bike Choice: {bike_decision}"

            accepted_treatments.append({
                'round_number': p.round_number,
                'treatment': p.treatment,
                'bonus_info': bonus_info,
            })
        player_in_final_round = self.in_round(Constants.num_rounds)
        # --- THE FIX IS HERE ---
        # 1. Regenerate the exact same list of tiles shown to the player by calling the new helper method.
        job_packages_for_display = player_in_final_round.get_dynamic_job_packages()
        
        # 2. Safely get the chosen index and find the corresponding package info.
        final_package_index = player_in_final_round.field_maybe_none('chosen_job_package_index')
        chosen_package_info = None
        if final_package_index is not None and final_package_index < len(job_packages_for_display):
            chosen_package_info = job_packages_for_display[final_package_index]
        
        time_log_data = player_in_final_round.field_maybe_none('modal_time_log')
        
        preferred_title = "Not chosen"
        preferred_job_index = player_in_round_1.field_maybe_none('chosen_job_tile')
        if preferred_job_index is not None and preferred_job_index < len(Constants.JOB_TILES):
            preferred_title = Constants.JOB_TILES[preferred_job_index]['title']

        parsed_time_log = None
        if time_log_data:
            try:
                parsed_time_log = json.loads(time_log_data)
            except json.JSONDecodeError:
                parsed_time_log = {'Error': 'Could not parse time log data.'}

        # Multiply the monthly willingness to pay by 12 for yearly display on results summary
        yearly_wtp_gym = player_in_round_1.willingness_to_pay_gym * 12
        yearly_wtp_bike = player_in_round_1.willingness_to_pay_bike * 12

        # 4. Construct the final dictionary for the template.
        return dict(
            accepted_treatments=accepted_treatments,
            chosen_package_info=chosen_package_info,
            preferred_title=preferred_title,
            parsed_time_log=parsed_time_log,
            modal_time_log=time_log_data,
            preferred_salary=player_in_round_1.preferred_salary,
            willingness_to_pay_gym=yearly_wtp_gym,  # Now displays the yearly amount
            willingness_to_pay_bike=yearly_wtp_bike,  # Now displays the yearly amount
            benefit_ranking=player_in_round_1.field_maybe_none('benefit_ranking'), # Show ranking on results
        )

# =============================================================================
# 3. PAGE SEQUENCE
# =============================================================================
page_sequence = [
    Introduction,
    ValuePerception,
    JobPreference,
    BenefitRanking, # New page added to the sequence
    JobOffer,
    JobSelection,
    ResultsSummary
]