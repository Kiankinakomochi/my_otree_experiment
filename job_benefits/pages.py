from otree.api import *
from .models import Constants

class Introduction(Page):
    pass


class JobOffer(Page):
    pass

class BonusChoice(Page):
    pass


class JobTiles(Page):
    pass


class ResultsSummary(Page):
    pass


page_sequence = [Introduction, JobOffer, BonusChoice, JobTiles, ResultsSummary]