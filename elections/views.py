from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import JsonResponse

from .forms import VoteCollegeChoiceForm, VotingForm
from .models import ElectionSeason, College, RunningCandidate


def index(request):
    """
    Homepage of the application.
    """
    current_election_season = ElectionSeason.objects.get(status="INITIATED")
    return render(request, 'elections/index.html',
                  {'current_election_season': current_election_season})


def vote_step_first(request):
    """
    First step of the voting process. Displays and processes the
    voter's college.
    """

    # Check first if there is an existing election season
    current_election_season = ElectionSeason.objects.get(status="INITIATED")
    if not current_election_season:
        return render(request, 'elections/no_election_season.html',
                      {})

    # If method is GET, initialize form for voter to choose his/her college
    if request.method == 'GET':
        college_choice_form = VoteCollegeChoiceForm()

    # Otherwise, process the choice
    else:
        college_choice_form = VoteCollegeChoiceForm(request.POST)

        if college_choice_form.is_valid():
            # Save choice to session
            request.session['choice_college_id'] \
                = college_choice_form.cleaned_data['college_of_voter'].id
            # Redirect to step 2
            return redirect(reverse('elections:vote_step_second'))

    return render(request, 'elections/vote_step_first.html',
                  {'college_choice_form': college_choice_form})


def vote_step_second(request):
    """
    Second step of the voting process. Displays and processes the
    voter's ballot.
    """

    # Check first if there is an existing election season
    current_election_season = (ElectionSeason.objects
        .prefetch_related("offeredposition_set",
                          "offeredposition_set__government_position",
                          "offeredposition_set__government_position__college",
                          "runningcandidate_set",
                          "runningcandidate_set__candidate",
                          "runningcandidate_set__government_position")
        .get(status="INITIATED"))
    if not current_election_season:
        return render(request, 'elections/no_election_season.html',
                      {})

    # Check if a college is already chosen by voter prior to proceeding
    if 'choice_college_id' not in request.session:
        return redirect(reverse('elections:vote_step_first'))

    # If method is GET, initialize the voting form
    if request.method == 'GET':
        # Fetch chosen college of voter from step 1 stored in session
        college = College.objects.get(pk=request.session['choice_college_id'])

        voting_form = VotingForm(election_season=current_election_season,
                                 college=college)

    # Otherwise, process the form submitted
    else:
        # TODO: Process voting form here
        voting_form = VotingForm(request.POST, college=college,
                                 election_season=current_election_season)

    return render(request, 'elections/vote_step_second.html',
                  {'voting_form': voting_form})


def confirm_selected_candidates(request):
    ids = request.GET.getlist('ids')

    running_candidates = (RunningCandidate.objects.filter(pk__in=ids)
        .select_related('candidate',
                        'government_position',
                        'government_position__college'))

    candidates_per_position = {}

    for running_candidate in running_candidates:
        position_college = running_candidate.government_position.college

        position_name = (
            (position_college.name if position_college else 'CENTRAL')
            + ' - '
            + running_candidate.government_position.name)

        if position_name not in candidates_per_position:
            candidates_per_position[position_name] = []
        
        candidates_per_position[position_name].append(
            f"{running_candidate.candidate.first_name} " \
            f"{running_candidate.candidate.last_name}")

    return JsonResponse(candidates_per_position)
