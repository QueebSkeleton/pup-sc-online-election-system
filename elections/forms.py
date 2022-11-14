from django import forms

from .models import College


class VoteCollegeChoiceForm(forms.Form):
    college_of_voter = forms.ModelChoiceField(queryset=College.objects.all())


class VotingForm(forms.Form):
    def __init__(self, *args, **kwargs):
        # Get election season from here
        election_season = kwargs.pop('election_season')
        college = kwargs.pop('college')

        super().__init__(*args, **kwargs)

        # Filter the election season's running candidates
        # based on the voter's college,
        # then create choice fields for each position
        running_candidates = {}
        for running_candidate in election_season.runningcandidate_set:
            if running_candidate.government_position.id not in running_candidates:
                running_candidates[running_candidate.government_position.id] \
                    = []
            
            # Insert to running candidates if it runs on CENTRAL (null value)
            # or on the same college as the voter
            if running_candidate.government_position.college == college:
                running_candidates[running_candidate.government_position.id] \
                    .append(running_candidate)

        # TODO: Create the form fields per position

    def clean(self):
        pass
