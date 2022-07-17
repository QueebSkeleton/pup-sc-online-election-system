from django.db import models
from django.contrib.auth import models as auth_models

from jsoneditor.fields.django3_jsonfield import JSONField

class College(models.Model):
    """
    A College situated in the Polytechnic University of the Philippines.
    """
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)


class PoliticalParty(models.Model):
    """
    A political organization established by students pursuing a specific
    ideology and agenda for the studentry.
    """
    name = models.CharField(max_length=255)
    is_renewed = models.BooleanField()
    current_officials = JSONField()


class GovernmentPosition(models.Model):
    """
    A position in the Student Council government. It is either a central
    or a college student council position.
    """
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    college = models.ForeignKey(to=College, on_delete=models.PROTECT)


class Candidate(models.Model):
    """
    A recognized candidate after filing its Certificate of Candidacy
    and is lawfully processed.
    """
    student_number = models.CharField(max_length=15)
    college = models.ForeignKey(to=College, on_delete=models.PROTECT)
    party = models.ForeignKey(to=PoliticalParty, on_delete=models.PROTECT)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    contact = models.CharField(max_length=255)
    image = models.ImageField()


class ElectionSeason(models.Model):
    """
    An election scenario in the context of the system. The system is designed
    to host multiple elections by handling its states and details.
    """
    academic_year = models.CharField(max_length=255)
    status = models.CharField(max_length=10,
                              choices=(('NEW', 'New'),
                                       ('ONGOING', 'Ongoing'),
                                       ('CONCLUDED', 'Concluded')))
    tallied_results = JSONField()
    offered_positions = models.ManyToManyField(to=GovernmentPosition,
                                               through='OfferedPosition')
    running_candidates = models.ManyToManyField(to=Candidate,
                                                through='RunningCandidate')
    initiated_on = models.DateTimeField()
    concluded_on = models.DateTimeField()


class OfferedPosition(models.Model):
    """
    An offered position in an election scenario. It also dictates how
    many of such position needs to be elected.
    """
    election_season = models.ForeignKey(to=ElectionSeason,
                                        on_delete=models.PROTECT)
    government_position = models.ForeignKey(to=GovernmentPosition,
                                            on_delete=models.PROTECT)
    max_positions_to_fill = models.PositiveSmallIntegerField()


class RunningCandidate(models.Model):
    """
    A candidate that runs for the specified election scenario. Its ballot
    number is dictated by COMELEC in regular processes, and is manually
    inputted.
    """
    election_season = models.ForeignKey(to=ElectionSeason,
                                        on_delete=models.PROTECT)
    candidate = models.ForeignKey(to=Candidate,
                                  on_delete=models.PROTECT)
    government_position = models.ForeignKey(to=GovernmentPosition,
                                            on_delete=models.PROTECT)
    ballot_number = models.PositiveSmallIntegerField()
    is_disqualified = models.BooleanField()
    disqualification_reason = models.TextField(null=True, blank=True)


class Ballot(models.Model):
    """
    A voter's evidence of voting.
    TODO: Should contain cryptographic signature.
    """
    election_season = models.ForeignKey(to=ElectionSeason,
                                        on_delete=models.PROTECT)
    voter = models.ForeignKey(to=auth_models.User,
                              on_delete=models.PROTECT)
    casted_on = models.DateTimeField()


class VotedCandidate(models.Model):
    """
    A ballot's individual voted candidate.
    """
    ballot = models.ForeignKey(to=Ballot, on_delete=models.CASCADE)
    running_candidate = models.ForeignKey(to=RunningCandidate,
                                          on_delete=models.PROTECT)
