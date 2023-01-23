from django.contrib import admin, messages
from django.shortcuts import redirect, render
from django.urls import path, reverse
from django.utils import timezone
from django.utils.html import mark_safe

from django.contrib.auth import models as auth_models

from .models import College, GovernmentPosition, Candidate, OfferedPosition, \
    RunningCandidate, ElectionSeason, ElectionSeasonWinningCandidate, Ballot

from . forms import ManualEntryPreliminaryForm, VotingForm

import random


@admin.register(College)
class CollegeModelAdmin(admin.ModelAdmin):
    list_display = ('name',)


@admin.register(GovernmentPosition)
class GovernmentPositionModelAdmin(admin.ModelAdmin):
    list_display = ('name', 'college_description', 'description',)

    @admin.display
    def college_description(self, obj):
        return obj.college if obj.college else '- CENTRAL -'


@admin.register(Candidate)
class CandidateModelAdmin(admin.ModelAdmin):
    list_display = ('student_number', 'college', 'party', 'name',)

    @admin.display
    def name(self, obj):
        return "%s %s" % (obj.first_name, obj.last_name)


class OfferedPositionTabularInline(admin.TabularInline):
    model = OfferedPosition
    extra = 0
    min_num = 1


class RunningCandidateTabularInline(admin.TabularInline):
    model = RunningCandidate
    extra = 0
    min_num = 1


@admin.register(Ballot)
class BallotModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'voter_name', 'election_season', 'casted_on',
                    'receipt_link',)
    search_fields = ('id', 'voter__first_name', 'voter__last_name',)

    @admin.display(description='Voter Name')
    def voter_name(self, obj):
        return f"{obj.voter.first_name} {obj.voter.last_name}"

    @admin.display(description='Receipt')
    def receipt_link(self, obj):
        pdf_link = reverse("elections:ballot_pdf_receipt",
                           kwargs={"id": obj.id})
        return mark_safe(f'<a href="{pdf_link}" target="_blank">PDF</a>')


@admin.register(ElectionSeason)
class ElectionSeasonModelAdmin(admin.ModelAdmin):
    list_display = ('academic_year', 'status', 'initiated_on', 'concluded_on',
                    'manual_entry_link', 'manage_links',
                    'refresh_winners_link',)

    fields = ('academic_year',)
    inlines = [OfferedPositionTabularInline, RunningCandidateTabularInline, ]

    @admin.display(description='Manage')
    def manage_links(self, obj):
        if not obj.status:
            return mark_safe(
                f'<a href="{obj.id}/initiate/"'
                f'onclick="return confirm(\'Initiate election season {obj}?\')"'
                '>Initiate</a>')
        elif obj.status == "INITIATED":
            return mark_safe(
                f'<a href="{obj.id}/conclude/"'
                f'onclick="return confirm(\'Conclude election season {obj}?\')">'
                f'Conclude</a>')
        elif obj.status == "CONCLUDED":
            return mark_safe(f'<a href="{obj.id}/results/">View Results</a>')
        else:
            return "N/A"

    @admin.display(description='Manual Entry')
    def manual_entry_link(self, obj):
        if obj.status == "INITIATED":
            return mark_safe(
                f'<a href="{obj.id}/ballot/step-1/">Manual Entry</a>')
        else:
            return "N/A"

    @admin.display(description='Refresh winners')
    def refresh_winners_link(self, obj):
        if obj.status == "CONCLUDED":
            return mark_safe(
                f'<a href="{obj.id}/refresh-winners/"'
                f'onclick="return confirm(\'Refresh winners'
                f'of election season {obj}?\')">Refresh</a>')
        else:
            return "N/A"

    def get_urls(self):
        # TODO: Add views for initiating and concluding an election.
        urls = [
            path('<int:pk>/initiate/',
                 self.admin_site.admin_view(
                     self.initiate_season_view)),
            path('<int:pk>/ballot/step-1/',
                 self.admin_site.admin_view(
                     self.manual_entry_first_step_view)),
            path('<int:pk>/ballot/step-2/',
                 self.admin_site.admin_view(
                     self.manual_entry_second_step_view)),
            path('<int:pk>/conclude/',
                 self.admin_site.admin_view(
                     self.conclude_season_view)),
            path('<int:pk>/refresh-winners/',
                 self.admin_site.admin_view(
                     self.refresh_winners_view)),
            path('<int:pk>/results/',
                 self.admin_site.admin_view(
                     self.results_season_view)),
        ] + super().get_urls()
        return urls

    def initiate_season_view(self, request, pk):
        election_season = ElectionSeason.objects.get(pk=pk)

        # If status is past initiation, then do nothing.
        if election_season.status != None:
            messages.add_message(
                request, messages.WARNING,
                f'Election Season {election_season}'
                ' cannot be initiated.')
            return redirect(
                reverse('admin:elections_electionseason_changelist'))

        # Check if another election season is initiated.
        another_initiated_season \
            = ElectionSeason.objects.filter(status='INITIATED').first()
        if another_initiated_season:
            messages.add_message(
                request, messages.WARNING,
                'Cannot initiate an election season when another is ongoing.')
            return redirect(
                reverse('admin:elections_electionseason_changelist'))

        election_season.status = 'INITIATED'
        election_season.initiated_on = timezone.now()
        election_season.save()

        messages.add_message(request, messages.SUCCESS,
                             f'Election Season {election_season} '
                             f'has been initiated.')
        return redirect(
            reverse('admin:elections_electionseason_changelist'))

    def manual_entry_first_step_view(self, request, pk):
        if request.method == 'POST':
            form = ManualEntryPreliminaryForm(request.POST)

            if form.is_valid():
                data = form.cleaned_data
                response = redirect("../step-2/")
                response['Location'] += (
                    '?voter_id='
                    + str(data['voter'].id)
                    + "&college_id="
                    + str(data['college_of_voter'].id))
                return response

        else:
            form = ManualEntryPreliminaryForm()

        election_season = ElectionSeason.objects.get(pk=pk)
        return render(
            request,
            'admin/elections/electionseason/manual_entry_first_step.html',
            {'title': 'Manual Entry First Step',
             'election_season': election_season, 'form': form})

    def manual_entry_second_step_view(self, request, pk):
        if not all(key in request.GET for key in ['voter_id', 'college_id']):
            return redirect('../step-1/')

        election_season = (ElectionSeason.objects.prefetch_related(
            "offeredposition_set",
            "offeredposition_set__government_position",
            "offeredposition_set__government_position__college",
            "runningcandidate_set",
            "runningcandidate_set__candidate",
            "runningcandidate_set__government_position")
            .get(pk=pk))
        voter = auth_models.User.objects.get(pk=request.GET.get('voter_id'))
        college = College.objects.get(pk=request.GET.get('college_id'))

        # Check if inputted user already has a ballot.
        if Ballot.objects.filter(election_season=election_season,
                                 voter=voter).first() != None:
            messages.add_message(
                request, messages.WARNING,
                f'User {voter} has already casted '
                f'its votes for this election.')
            return redirect(
                reverse("admin:elections_electionseason_changelist"))

        if request.method == 'GET':
            voting_form = VotingForm(election_season=election_season,
                                     college=college)

        elif request.method == 'POST':
            voting_form = VotingForm(request.POST, college=college,
                                     election_season=election_season)

            if voting_form.is_valid():
                # Extract all voted candidates from form
                voted_candidates = [voted_candidate for position_candidates
                                    in list(voting_form.cleaned_data.values())
                                    for voted_candidate
                                    in position_candidates]

                # Construct then save the ballot object
                ballot = Ballot(election_season=election_season,
                                college=college,
                                voter=voter,
                                casted_on=timezone.now())
                ballot.save()
                # Set the voted candidates of this ballot
                # then trigger another save
                ballot.voted_candidates.add(*voted_candidates)
                # Add message
                messages.add_message(
                    request, messages.SUCCESS,
                    f'Ballot for user {ballot.voter} has been saved.')
                return redirect(
                    reverse("admin:elections_electionseason_changelist"))

        return render(
            request,
            'admin/elections/electionseason/manual_entry_second_step.html',
            {'election_season': election_season, 'voting_form': voting_form})

    def get_tally(self, election_season):
        # Initialize tally to 0 votes per candidate
        tally = {running_candidate.id: running_candidate
                 for running_candidate
                 in election_season.runningcandidate_set.all()}
        for running_candidate in tally.values():
            running_candidate.tallied_votes = 0

        # Go through each ballot's votes, add to tally
        # TODO: Validate if ballot is tampered (digest + public key)
        for ballot in election_season.ballot_set.all():
            for voted_candidate in ballot.voted_candidates.all():
                tally[voted_candidate.id].tallied_votes += 1

        return tally

    def get_winners(self, election_season, tally):
        winners = []
        # While calculating the winners, ties are inevitable.
        # The tiebreaking enforced in here is a random.choice
        # which is the same as a real-life coin toss done by most states.
        # The chosen winner's tallied votes will be increased by one
        # just so the system easily recognizes it as the winner.
        # The candidates with updated tallies will be stored in this variable,
        # which should be saved by the caller.
        candidates_to_update = []

        for offered_position in election_season.offeredposition_set.all():
            candidates_for_pos = election_season.runningcandidate_set.filter(
                government_position=offered_position.government_position)

            # Find the winners of this position
            # (uses a list to handle the possibility of ties)
            pos_winners = []
            for running_candidate in candidates_for_pos:
                # Add to winners if either it is empty
                # or if this candidate ties with the current winners
                if len(pos_winners) == 0 \
                    or tally[pos_winners[0].id].tallied_votes \
                        == tally[running_candidate.id].tallied_votes:
                    pos_winners.append(running_candidate)

                # Override the winners if this candidate has more votes
                elif tally[pos_winners[0].id].tallied_votes \
                        < tally[running_candidate.id].tallied_votes:
                    pos_winners.clear()
                    pos_winners.append(running_candidate)

            # If there are ties, randomly pick a winner
            # (like simulating a real-life toin coss for tiebreaking)
            # TODO: Consult with an elections expert
            #       of the conducting state
            if len(pos_winners) > 1:
                pos_winner = random.choice(pos_winners)
                pos_winner.tallied_votes += 1
                candidates_to_update.append(pos_winner)
            else:
                pos_winner = pos_winners[0]

            # Save the winner
            government_position = offered_position.government_position
            # Student council name
            student_council \
                = "CENTRAL" if not government_position.college \
                else government_position.college.name
            # Position name
            position_name = f'{student_council} - ' \
                            f'{offered_position.government_position.name}'

            # Candidate name
            candidate = pos_winner.candidate
            candidate_name = f'{candidate.first_name} ' \
                f'{candidate.last_name}'

            winning_candidate = ElectionSeasonWinningCandidate(
                election_season=election_season,
                running_candidate=pos_winner,
                position_name=position_name,
                ballot_number=pos_winner.ballot_number,
                candidate_name=candidate_name)
            winners.append(winning_candidate)

        return winners, candidates_to_update

    def conclude_season_view(self, request, pk):
        election_season = (
            ElectionSeason.objects.filter(pk=pk)
            .prefetch_related(
                'ballot_set',
                'ballot_set__voted_candidates',
                'offeredposition_set',
                'offeredposition_set__government_position',
                'offeredposition_set__government_position__college',
                'runningcandidate_set',
                'runningcandidate_set__candidate',
                'runningcandidate_set__government_position')[0])

        # If status is not 'INITIATED', do nothing.
        if election_season.status != 'INITIATED':
            messages.add_message(
                request, messages.WARNING,
                f'Election Season {election_season}'
                ' cannot be concluded.')
            return redirect(
                reverse('admin:elections_electionseason_changelist'))

        election_season.concluded_on = timezone.now()
        election_season.status = 'CONCLUDED'
        election_season.save()

        # Tally the results then merge it to the objects
        tally = self.get_tally(election_season)
        # Get the winners while resolving ties
        winners, candidates_to_update = self.get_winners(
            election_season, tally)

        # Save the tally
        for running_candidate in tally.values():
            running_candidate.save()
        # After resolving the ties, reupdate the candidate tallies
        for running_candidate in candidates_to_update:
            running_candidate.save()
        # Save the winners
        for winning_candidate in winners:
            winning_candidate.save()

        messages.add_message(
            request, messages.SUCCESS,
            f'Election Season {election_season} has been concluded.')
        return redirect(reverse('admin:elections_electionseason_changelist'))

    def refresh_winners_view(self, request, pk):
        election_season = (
            ElectionSeason.objects.filter(pk=pk)
            .prefetch_related(
                'offeredposition_set',
                'offeredposition_set__government_position',
                'offeredposition_set__government_position__college',
                'runningcandidate_set',
                'runningcandidate_set__candidate',
                'runningcandidate_set__government_position',
                'electionseasonwinningcandidate_set')[0])

        # Extract tally
        tally = {running_candidate.id: running_candidate
                 for running_candidate
                 in election_season.runningcandidate_set.all()}
        # Get the winners
        winners, candidates_to_update = self.get_winners(
            election_season, tally)

        # Refresh the winners
        election_season.electionseasonwinningcandidate_set.all().delete()
        for running_candidate in candidates_to_update:
            running_candidate.save()
        for winning_candidate in winners:
            winning_candidate.save()

        messages.add_message(
            request, messages.SUCCESS,
            f'Election Season {election_season} '
            f'winners have been recalculated.')
        return redirect(reverse('admin:elections_electionseason_changelist'))

    def results_season_view(self, request, pk):
        election_season = ElectionSeason.objects.get(pk=pk)

        # Construct a results list, structured like the ff:
        # [
        #   { position: GovernmentPosition obj,
        #     running_candidates: [
        #       { running_candidate: RunningCandidate,
        #         vote_percentage: float },
        #       { ... next candidate }
        #     ],
        #     winning_candidates: [ WinningCandidate obj, ... ]
        #   },
        #   { ... next position candidates and winners }
        # ]
        results = []

        for offered_position in election_season.offeredposition_set.all():
            govt_pos = offered_position.government_position

            position_summary = {
                'position': govt_pos,
                'running_candidates': []
            }

            running_candidates_for_pos = \
                (election_season.runningcandidate_set.filter(
                    government_position=govt_pos))
            # Get the total votes
            total = 0
            for running_candidate in running_candidates_for_pos:
                total += running_candidate.tallied_votes
            # Plug each candidate to the summary
            # with the candidate's percentage of votes garnered
            for running_candidate in running_candidates_for_pos:
                vote_percentage = running_candidate.tallied_votes / total
                position_summary['running_candidates'].append({
                    'running_candidate': running_candidate,
                    'vote_percentage': vote_percentage
                })
            # Plug each winning candidate to the summary
            position_summary['winning_candidates'] = \
                list(election_season
                     .electionseasonwinningcandidate_set
                     .filter(
                         running_candidate__government_position=govt_pos))

            results.append(position_summary)

        return render(
            request,
            'admin/elections/electionseason/statistics.html',
            {"title": f"Results of Election Season {election_season}",
             "election_season": election_season, "results": results})
