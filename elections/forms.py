from django import forms
from django.utils.html import mark_safe
from django.contrib.auth import models as auth_models

from .models import College


class VoteCollegeChoiceForm(forms.Form):
    """
    Form for a voter to choose which college he/she came from.
    """
    college_of_voter = forms.ModelChoiceField(queryset=College.objects.all())


class ManualEntryPreliminaryForm(forms.Form):
    """
    Form for manual entry where admin is prompted for a user and a college.
    """
    voter = forms.ModelChoiceField(queryset=auth_models.User.objects.all())
    college_of_voter = forms.ModelChoiceField(queryset=College.objects.all())


class CandidateMultipleChoiceField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        return mark_safe(
            "<img src='"
            + (obj.candidate.image.url if obj.candidate.image
                else 'https://via.placeholder.com/150')
            + "' class='img-fluid' />"
            + "<p class='text-center'>"
            + f"#{obj.ballot_number} - "
            + f"{obj.candidate.first_name} "
            + obj.candidate.last_name
            + "</p>")


class VotingForm(forms.Form):
    """
    Form used by a voter to pick candidates.
    Has dynamic multiple choice fields (checkbox)
    for each of an election season's offered positions.
    """

    def __init__(self, *args, **kwargs):
        election_season = kwargs.pop('election_season')
        voter_college = kwargs.pop('college')
        use_custom_candidate_field = kwargs.pop('use_custom_candidate_field',
                                                False)

        super().__init__(*args, **kwargs)

        # For each position offered in this election season,
        # create a multiple choice field  with the candidates as the choices.
        for offered_position in election_season.offeredposition_set.all():

            position_college = offered_position.government_position.college

            # Only create a field for positions that belong
            # either in CENTRAL SC or in the same college SC as the voter,
            # and if there are actual running candidates in that position.
            if position_college == None or position_college == voter_college:
                candidates_queryset \
                    = (election_season.runningcandidate_set
                       .filter(government_position=offered_position
                               .government_position))

                if candidates_queryset.count() > 0:
                    field_name \
                        = ((position_college.name.replace(' ', '').lower()
                            if position_college else 'central')) \
                        + "_" + (offered_position.government_position.name
                                 .replace(' ', '').lower())

                    field_label \
                        = ((position_college.name
                            if position_college else 'Central')) \
                        + " - " + offered_position.government_position.name

                    self.fields[field_name] \
                        = (CandidateMultipleChoiceField(
                            queryset=candidates_queryset)
                           if use_custom_candidate_field else
                           forms.ModelMultipleChoiceField(
                            queryset=candidates_queryset))

                    self.fields[field_name].label = field_label
