from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import JsonResponse
from django.utils import timezone
from django.contrib import messages

from .forms import VoteCollegeChoiceForm, VotingForm
from .models import ElectionSeason, College, RunningCandidate, Ballot

# TODO: Use view decorators for checking for current election season,
#       and if voter has voted.


def index(request):
    """
    Homepage of the application.
    """
    # Get initiated election season (will be set to None if there aren't)
    current_election_season \
        = ElectionSeason.objects.filter(status="INITIATED").first()
    # Flag if voter has already voted for this election season
    has_already_voted = False
    if request.user.is_authenticated and current_election_season:
        has_already_voted \
            = Ballot.objects.filter(election_season=current_election_season,
                              voter=request.user).first() != None
    return render(request, 'elections/index.html',
                  {'current_election_season': current_election_season,
                   'has_already_voted': has_already_voted})


def vote_step_first(request):
    """
    First step of the voting process. Displays and processes the
    voter's college.
    """

    # Check if logged in
    # TODO: Refactor to a decorator
    if not request.user.is_authenticated:
        messages.add_message(request, messages.WARNING,
        'Login first to your Microsoft Webmail account prior to voting.')
        return redirect(reverse('elections:index'))

    # Check first if there is an existing election season
    current_election_season \
        = ElectionSeason.objects.filter(status='INITIATED').first()
    if not current_election_season:
        messages.add_message(request, messages.WARNING,
            'You are trying to vote when there is no ongoing election.')
        return redirect(reverse('elections:index'))

    # Check if voter has already voted for this election season
    if Ballot.objects.filter(election_season=current_election_season,
        voter=request.user).first() != None:
        messages.add_message(request, messages.WARNING,
            'You have already voted for this election.')
        return redirect(reverse('elections:index'))

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
    # TODO: Refactor to a decorator
    if not request.user.is_authenticated:
        messages.add_message(request, messages.WARNING,
        'Login first to your Microsoft Webmail account prior to voting.')
        return redirect(reverse('elections:index'))

    # Check first if there is an existing election season
    current_election_season \
        = (ElectionSeason.objects
           .prefetch_related("offeredposition_set",
                             "offeredposition_set__government_position",
                             "offeredposition_set__government_position__college",
                             "runningcandidate_set",
                             "runningcandidate_set__candidate",
                             "runningcandidate_set__government_position")
           .filter(status="INITIATED")).first()
    if not current_election_season:
        messages.add_message(request, messages.WARNING,
            'You are trying to vote when there is no ongoing election.')
        return redirect(reverse('elections:index'))

    # Check if voter has already voted for this election season
    if Ballot.objects.filter(election_season=current_election_season,
        voter=request.user).first() != None:
        messages.add_message(request, messages.WARNING,
            'You have already voted for this election.')
        return redirect(reverse('elections:index'))

    # Check if a college is already chosen by voter prior to proceeding
    if 'choice_college_id' not in request.session:
        return redirect(reverse('elections:vote_step_first'))

    # Fetch chosen college of voter from step 1 stored in session
    college = College.objects.get(pk=request.session['choice_college_id'])

    # If method is GET, initialize the voting form
    if request.method == 'GET':
        voting_form = VotingForm(election_season=current_election_season,
                                 college=college,
                                 use_custom_candidate_field=True)

    # Otherwise, process the form submitted
    else:
        voting_form = VotingForm(request.POST, college=college,
                                 election_season=current_election_season)

        if voting_form.is_valid():
            # Extract all voted candidates from form
            voted_candidates = [voted_candidate for position_candidates
                                in list(voting_form.cleaned_data.values())
                                for voted_candidate in position_candidates]

            # Construct then save the ballot object
            ballot = Ballot(election_season=current_election_season,
                            voter=request.user,
                            casted_on=timezone.now())
            ballot.save()
            # Set the voted candidates of this ballot
            # then trigger another save
            ballot.voted_candidates.set(voted_candidates)
            ballot.save()
            # TODO: Validate signature with public key
            return render(request, 'elections/vote_conclusion.html', {})

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
            f"#{running_candidate.ballot_number} - "
            f"{running_candidate.candidate.first_name} "
            f"{running_candidate.candidate.last_name}")

    return JsonResponse(candidates_per_position)
