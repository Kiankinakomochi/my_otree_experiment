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
            description='As an Analyst, you will be responsible for collecting, interpreting, and presenting data to help the organization make informed decisions. This role requires strong analytical skills and attention to detail.',
        ),
        dict(
            title='Developer',
            wage=3300,
            description='As a Developer, you will design, build, and maintain software applications and systems. You will work on coding, testing, and debugging to create efficient and scalable solutions.',
        ),
        dict(
            title='Consultant',
            wage=3100,
            description='As a Consultant, you will provide expert advice and strategic solutions to clients across various industries. This involves identifying problems, developing recommendations, and assisting with implementation.',
        ),
        dict(
            title='Manager',
            wage=3500,
            benefits=['Childcare support', 'Health program'],
            description='As a Manager, you will lead a team, oversee projects, and make key strategic decisions to achieve organizational goals. This role demands strong leadership, communication, and organizational skills.',
        ),
    ]
    
    # NEW: Benefit packages for each job title for the revised JobSelection page
    BENEFIT_PACKAGES = {
        'Analyst': [
            dict(name='Health & Wellness', benefits=['Gym Membership', 'Health program'], wage_adjustment=0, description="Focuses on physical and mental well-being."),
            dict(name='Work-Life Balance', benefits=['Flexible hours', 'Extra vacation days'], wage_adjustment=-100, description="Provides more flexibility and time off."),
            dict(name='Commuter Plus', benefits=['Public transport ticket', 'Work Bike'], wage_adjustment=-50, description="Eases your daily commute."),
        ],
        'Developer': [
            dict(name='Tech Focused', benefits=['Training courses', 'Work Bike'], wage_adjustment=0, description="Supports continuous learning and a healthy commute."),
            dict(name='Family First', benefits=['Childcare support', 'Flexible hours'], wage_adjustment=-150, description="Offers support for family responsibilities."),
            dict(name='Peak Performer', benefits=['Health program', 'Extra vacation days'], wage_adjustment=-100, description="Maximizes wellness and personal time."),
        ],
        'Consultant': [
            dict(name='The Traveler', benefits=['Public transport ticket', 'Extra vacation days'], wage_adjustment=0, description="Ideal for those always on the move."),
            dict(name='Skill Builder', benefits=['Training courses', 'Gym Membership'], wage_adjustment=-50, description="Invests in your professional and personal growth."),
            dict(name='Flexible Professional', benefits=['Flexible hours', 'Work Bike'], wage_adjustment=-75, description="Combines schedule flexibility with a sustainable commute."),
        ],
        'Manager': [
            dict(name='Executive Health', benefits=['Health program', 'Gym Membership'], wage_adjustment=0, description="A premium package for health and wellness."),
            dict(name='Family Leader', benefits=['Childcare support', 'Flexible hours'], wage_adjustment=-200, description="Comprehensive support for managers with families."),
            dict(name='Strategic Growth', benefits=['Training courses', 'Extra vacation days'], wage_adjustment=-150, description="Focuses on leadership development and rejuvenation."),
        ],
    }


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

    # NEW: Fields for the JobTitleSurvey page (shown in round 1)
    preferred_job_title = models.StringField(
        label="Please select your preferred job title from the options below:",
        choices=[job['title'] for job in Constants.JOB_TILES],
        widget=widgets.RadioSelect,
        blank=True
    )
    preferred_salary = models.CurrencyField(
        label="What is your preferred minimum annual salary for this role?",
        min=0,
        blank=True
    )

    # CHANGED: This field is now for the benefit package, not the job tile.
    chosen_benefit_package = models.IntegerField(
        label="Please select your preferred benefit package.",
        widget=widgets.RadioSelect, # Choices are set dynamically in the Page class
        blank=True
    )
    
    # Fields for the 'Choice' treatment
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
        return self.round_number == 1

# NEW PAGE: This page surveys the user for their preferred job title and salary.
class JobTitleSurvey(Page):
    form_model = 'player'
    form_fields = ['preferred_job_title', 'preferred_salary']

    def is_displayed(self):
        # Display only in the first round, after value perception.
        return self.round_number == 1

    def vars_for_template(self):
        # Pass job descriptions to the template to help the user choose.
        return dict(job_tiles=Constants.JOB_TILES)


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

# MODIFIED PAGE: This page now shows benefit packages for the chosen job title.
class JobSelection(Page):
    form_model = 'player'
    # --- ADDED `modal_time_log` TO THE FORM FIELDS ---
    form_fields = ['chosen_job_tile', 'modal_time_log']

    def is_displayed(self):
        # Only display this page in the final round
        return self.round_number == Constants.num_rounds

    def get_form(self, *args, **kwargs):
        # This method dynamically sets the choices for the radio buttons
        # based on the job title selected by the player in round 1.
        form = super().get_form(*args, **kwargs)
        player_r1 = self.in_round(1)
        
        # Default to first job if player somehow skipped the survey
        chosen_title = player_r1.preferred_job_title or Constants.JOB_TILES[0]['title']
        
        packages = Constants.BENEFIT_PACKAGES.get(chosen_title, [])
        # Choices are a list of tuples: (value, label)
        # Here, value is the index of the package.
        choices = [(i, pkg['name']) for i, pkg in enumerate(packages)]
        form.fields['chosen_benefit_package'].choices = choices
        return form


    def vars_for_template(self):
        player_r1 = self.in_round(1)
        chosen_title = player_r1.preferred_job_title or Constants.JOB_TILES[0]['title']
        
        # Find the base wage for the chosen title
        job_info = next((job for job in Constants.JOB_TILES if job['title'] == chosen_title), None)
        base_wage = job_info['wage'] if job_info else 0
        
        # Get packages and their descriptions
        packages_with_details = Constants.BENEFIT_PACKAGES.get(chosen_title, [])

        return dict(
            job_title=chosen_title,
            base_wage=base_wage,
            packages=packages_with_details,
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
                if p.gym_choice in ['Cash', 'Benefit'] or p.bike_choice in ['Cash', 'Benefit']:
                     accepted_info = "Yes (at least one)"
            else: # Covers 'Cash Bonus' and 'Non-Monetary Perk'
                if p.treatment == 'Non-Monetary Perk':
                    bonus_info = p.perk_offered or "N/A"
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

        # --- Get final job and benefit selection ---
        player_r1 = self.in_round(1)
        player_final = self.in_round(Constants.num_rounds)
        
        preferred_title = player_r1.field_maybe_none('preferred_job_title')
        package_index = player_final.field_maybe_none('chosen_benefit_package')
        
        chosen_package_info = None
        if preferred_title and package_index is not None:
            packages = Constants.BENEFIT_PACKAGES.get(preferred_title, [])
            if 0 <= package_index < len(packages):
                chosen_package_info = packages[package_index]

        return dict(
            accepted_treatments=accepted_treatments,
            preferred_job_title=preferred_title,
            preferred_salary=player_r1.field_maybe_none('preferred_salary'),
            chosen_benefit_package=chosen_package_info,
            modal_time_log=player_final.field_maybe_none('modal_time_log'),  
            willingness_to_pay_gym=player_r1.field_maybe_none('willingness_to_pay_gym'),
            willingness_to_pay_bike=player_r1.field_maybe_none('willingness_to_pay_bike'),
        )


# UPDATED page sequence
page_sequence = [
    Introduction, 
    ValuePerception, 
    JobTitleSurvey, # New page inserted here
    JobOffer, 
    JobSelection, 
    ResultsSummary
]
