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

    # --- NEW ---
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
        'Professional Development Budget': 'An annual budget of €1,000 to be spent on approved training courses, conferences, or books.',
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
    willingness_to_pay_gym = models.CurrencyField(
        label="What is the maximum amount you would be willing to pay per year for a premium gym membership (access to all facilities, classes, etc.)?",
        blank=False,
        min=0,
        max=10000,
    )
    willingness_to_pay_bike = models.CurrencyField(
        label="What is the maximum amount you would be willing to pay per year for a work bicycle (including maintenance and insurance)?",
        blank=False, min=0, max=10000
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

        # --- DYNAMIC TILE GENERATION LOGIC ---
        
        # 1. Get the participant's ranking and preferred salary from round 1
        ranked_benefits_str = player_in_round_1.field_maybe_none('benefit_ranking')
        preferred_salary = player_in_round_1.field_maybe_none('preferred_salary') or Constants.BASE_SALARY
        
        # Use WTP as the "Numéraire" for salary sacrifice
        wtp_sum = (player_in_round_1.field_maybe_none('willingness_to_pay_gym') or 0) + \
                  (player_in_round_1.field_maybe_none('willingness_to_pay_bike') or 0)

        # Get the preferred job title
        preferred_job_index = player_in_round_1.field_maybe_none('chosen_job_tile')
        chosen_title = "General Position"
        if preferred_job_index is not None:
            chosen_title = Constants.JOB_TILES[preferred_job_index]['title']
        
        # 1. Create packages for display with the consistent title
        job_packages_for_display = []
        
        # Fallback in case ranking data is missing
        if not ranked_benefits_str:
             # If no ranking, show some default tiles (or handle as an error)
             # Here, we revert to the old logic as a safe fallback.
            for i, original_job in enumerate(Constants.JOB_TILES):
                job_packages_for_display.append({
                    'title': chosen_title,
                    'wage': original_job['wage'],
                    'benefits_summary': [b for b in original_job.get('benefits', [])],
                    'index': i
                })
        else:
            # 2. Create the personalized tiers
            ranked_benefits = ranked_benefits_str.split(',')
            
            # Define salary tiers
            tier1_salary = preferred_salary
            # Prevent salary from going below zero if WTP is very high
            tier4_salary = max(0, preferred_salary - wtp_sum)
            salary_step = (tier1_salary - tier4_salary) / 3
            
            salaries = [
                round(tier1_salary),
                round(tier1_salary - salary_step),
                round(tier1_salary - 2 * salary_step),
                round(tier4_salary)
            ]
            
            # Define benefit tiers from the player's ranking
            # Tiers are: Top rank, second rank, third from bottom, second from bottom
            # This creates a more interesting choice than just 1,2,7,8
            num_ranked = len(ranked_benefits)
            benefit_tiers = [
                ranked_benefits[0],                   # Tier 1 Benefit (Rank #1)
                ranked_benefits[1],                   # Tier 2 Benefit (Rank #2)
                ranked_benefits[num_ranked - 3],    # Tier 3 Benefit (e.g., Rank #6 out of 8)
                ranked_benefits[num_ranked - 2],    # Tier 4 Benefit (e.g., Rank #7 out of 8)
            ]
            
            # 3. Build the 4 personalized job tiles
            # Tile 1: Tier 1 Salary, Tier 4 Benefit
            # Tile 2: Tier 2 Salary, Tier 3 Benefit
            # etc.
            for i in range(4):
                job_packages_for_display.append({
                    'title': chosen_title,
                    'wage': salaries[i],
                    'benefits_summary': [benefit_tiers[3-i]], # Inversely matched
                    'index': i,
                    'benefit_details': {
                        benefit_tiers[3-i]: Constants.BENEFIT_DESCRIPTIONS.get(benefit_tiers[3-i], '')
                    }
                })

        # The full data needs to be passed to the script for the modal pop-up
        job_tiles_for_script = job_packages_for_display
        
        return dict(
            # Data for displaying the tiles
            job_packages_for_display=job_packages_for_display,
            modal_time_log = self.field_maybe_none('modal_time_log'),
            job_tiles_for_script=job_tiles_for_script,
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
            
        # --- MODIFIED ---: Re-generating the chosen package info based on dynamic tiles
        chosen_package_info = None
        final_package_index = player_in_final_round.field_maybe_none('chosen_job_package_index')
        if final_package_index is not None:
             # Since tiles are dynamic, we reconstruct the chosen tile's data for display
             # This is a simplified reconstruction. For full data, one would need to rerun the generation logic.
            job_packages_for_display = self.vars_for_template()['job_packages_for_display']
            if final_package_index < len(job_packages_for_display):
                chosen_package_info = job_packages_for_display[final_package_index]

        time_log_data = player_in_final_round.field_maybe_none('modal_time_log')
        
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