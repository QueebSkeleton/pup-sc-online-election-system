from django.shortcuts import render, redirect
from django.urls import reverse

from django.contrib.auth.decorators import login_required

from .forms import VoteCollegeChoiceForm, VotingForm
from .models import ElectionSeason, College


def index(request):
    return render(request, 'elections/index.html', {})


# @login_required
def vote_step_first(request):
    # TODO: Check first if an election season is initiated
    if request.method == 'POST':
        college_choice_form = VoteCollegeChoiceForm(request.POST)

        if college_choice_form.is_valid():
            request.session['choice_college_id'] \
                = college_choice_form.cleaned_data['college_of_voter'].id
            return redirect(reverse('elections:vote_step_second'))

    else:
        college_choice_form = VoteCollegeChoiceForm()

    return render(request, 'elections/vote_step_first.html',
                  {'college_choice_form': college_choice_form})

# @login_required


def vote_step_second(request):
    # TODO: Check first if an election season is initiated

    if 'choice_college_id' not in request.session:
        return redirect(reverse('elections:vote_step_first'))

    # If POST, process form
    if request.method == 'POST':
        pass

    # If GET, initialize form
    else:
        current_election_season \
            = (ElectionSeason.objects.filter(status='INITIATED')
               .prefetch_related(
                'offeredposition_set',
                'runningcandidate_set',
                'runningcandidate_set__candidate',
                'runningcandidate_set__government_position',
                'runningcandidate_set__government_position__college'))[0]
        college = College.objects.get(pk=request.session['choice_college_id'])
        voting_form = VotingForm(election_season=current_election_season,
                                 college=college)

    return render(request, 'elections/vote_step_second.html',
                  {'voting_form': voting_form})
