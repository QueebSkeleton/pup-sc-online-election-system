from django.db import models
from django.contrib.auth import models as auth_models

from jsoneditor.fields.django3_jsonfield import JSONField


class College(models.Model):
    """
    A College situated in the Polytechnic University of the Philippines.
    """
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name


class GovernmentPosition(models.Model):
    """
    A position in the Student Council government. It is either a central
    or a college student council position.
    """
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    college = models.ForeignKey(
        to=College, on_delete=models.PROTECT, null=True, blank=True)
    to_fill = models.PositiveSmallIntegerField()

    def __str__(self):
        return f'{self.college.name + " - " if self.college else ""}{self.name}'

    class Meta:
        verbose_name = 'Government Position'


class Candidate(models.Model):
    """
    A recognized candidate after filing its Certificate of Candidacy
    and is lawfully processed.
    """
    student_number = models.CharField(max_length=15)
    college = models.ForeignKey(to=College, on_delete=models.PROTECT)
    party = models.CharField(max_length=255, null=True, blank=True)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    contact = models.CharField(max_length=255)
    image = models.ImageField()

    def __str__(self):
        return f'{self.student_number} - {self.first_name} {self.last_name}'


class ElectionSeason(models.Model):
    """
    An election scenario in the context of the system. The system is designed
    to host multiple elections by handling its states and details.
    """
    academic_year = models.CharField(max_length=255)
    status = models.CharField(null=True, blank=True, max_length=10,
                              choices=(('INITIATED', 'Initiated'),
                                       ('CONCLUDING', 'Concluding'),
                                       ('CONCLUDED', 'Concluded')))
    initiated_on = models.DateTimeField(null=True, blank=True)
    concluded_on = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:
        return self.academic_year

    class Meta:
        verbose_name = 'Election Season'


class OfferedPosition(models.Model):
    """
    An offered position in an election scenario. It also dictates how
    many of such position needs to be elected.
    """
    election_season = models.ForeignKey(to=ElectionSeason,
                                        on_delete=models.CASCADE)
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
                                        on_delete=models.CASCADE)
    candidate = models.ForeignKey(to=Candidate,
                                  on_delete=models.PROTECT)
    government_position = models.ForeignKey(to=GovernmentPosition,
                                            on_delete=models.PROTECT)
    ballot_number = models.PositiveSmallIntegerField()
    is_disqualified = models.BooleanField()
    disqualification_reason = models.TextField(null=True, blank=True)
    tallied_votes = models.PositiveIntegerField(null=True, blank=True)


class Ballot(models.Model):
    """
    A voter's evidence of voting.
    """
    election_season = models.ForeignKey(to=ElectionSeason,
                                        on_delete=models.PROTECT)
    voter = models.ForeignKey(to=auth_models.User,
                              on_delete=models.PROTECT)
    voted_candidates = models.ManyToManyField(to=RunningCandidate)
    casted_on = models.DateTimeField()
    signature = models.TextField(null=True, blank=True)
    public_key = models.TextField(null=True, blank=True)


class ElectionSeasonWinningCandidate(models.Model):
    """
    A result model (summary table) that resembles a winning candidate
    in an election season for a position.
    """
    election_season = models.ForeignKey(null=True, to=ElectionSeason,
                                        on_delete=models.SET_NULL)
    running_candidate = models.ForeignKey(null=True, to='RunningCandidate',
                                          on_delete=models.SET_NULL)
    # Duplicated fields for the sake of summary tables
    position_name = models.CharField(max_length=510)
    ballot_number = models.PositiveSmallIntegerField()
    candidate_name = models.CharField(max_length=510)
