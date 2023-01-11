from django.contrib import admin
from django.utils.html import mark_safe
from django.urls import path
from django.forms import BaseInlineFormSet
from django.http import JsonResponse
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone

from . import models


@admin.register(models.College)
class CollegeModelAdmin(admin.ModelAdmin):
    list_display = ('name',)


@admin.register(models.GovernmentPosition)
class GovernmentPositionModelAdmin(admin.ModelAdmin):
    list_display = ('name', 'college_description', 'description',)

    @admin.display
    def college_description(self, obj):
        return obj.college if obj.college else '- CENTRAL -'


@admin.register(models.Candidate)
class CandidateModelAdmin(admin.ModelAdmin):
    list_display = ('student_number', 'college', 'party', 'name',)

    @admin.display
    def name(self, obj):
        return "%s %s" % (obj.first_name, obj.last_name)


class OfferedPositionInlineFormset(BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        positions = models.GovernmentPosition.objects.all()
        kwargs['initial'] = [
            {'government_position': government_position,
             'max_positions_to_fill': government_position.to_fill}
            for government_position in positions
        ]
        print(kwargs['initial'])
        super(OfferedPositionInlineFormset, self).__init__(*args, **kwargs)


class OfferedPositionTabularInline(admin.TabularInline):
    model = models.OfferedPosition
    extra = 0
    min_num = 1
    formset = OfferedPositionInlineFormset

    def get_extra(self, request, obj=None, **kwargs):
        if obj:
            return (super(OfferedPositionTabularInline, self)
                    .get_extra(request, obj, **kwargs))

        count = models.GovernmentPosition.objects.count()
        return count - 1 if count > 0 else 0


class RunningCandidateTabularInline(admin.TabularInline):
    model = models.RunningCandidate
    extra = 0
    min_num = 1


@admin.register(models.ElectionSeason)
class ElectionSeasonModelAdmin(admin.ModelAdmin):
    list_display = ('academic_year', 'status', 'initiated_on', 'concluded_on',
                    'manage', 'override',)

    fields = ('academic_year',)
    inlines = [OfferedPositionTabularInline, RunningCandidateTabularInline, ]

    @admin.display()
    def manage(self, obj):
        if not obj.status:
            return mark_safe(
                f'<a href="{obj.id}/initiate/"'
                f'onclick="return confirm(\'Initiate election season {obj}?\')"'
                '>Initiate</a>')
        elif obj.status == "INITIATED":
            return mark_safe(
                f'<a href="{obj.id}/conclude/"'
                f'onclick="return confirm(\'Conclude election season {obj}?\')"'
                '>Conclude</a>')
        else:
            return "N/A"

    @admin.display()
    def override(self, obj):
        if obj.status == "CONCLUDED":
            return mark_safe(f'<a href="{obj.id}/override/">Override</a>')
        else:
            return "N/A"

    def get_urls(self):
        # TODO: Add views for initiating and concluding an election.
        urls = [
            path('<int:pk>/initiate/',
                 self.admin_site.admin_view(self.initiate_season_view)),
            path('<int:pk>/conclude/',
                 self.admin_site.admin_view(self.conclude_season_view)),
            path('<int:pk>/statistics/',
                 self.admin_site.admin_view(self.season_statistics_view)),
        ] + super().get_urls()
        return urls

    def initiate_season_view(self, request, pk):
        election_season = models.ElectionSeason.objects.get(pk=pk)

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
            = models.ElectionSeason.objects.filter(status='INITIATED').first()
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
                             f'Election Season {election_season} has been initiated.')
        return redirect(
            reverse('admin:elections_electionseason_changelist'))

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
                        > tally[running_candidate.id].tallied_votes:
                    pos_winners.clear()
                    pos_winners.append(running_candidate)

            # Construct objects for each winner,
            # then add to the final list of winners
            for winning_candidate in pos_winners:
                government_position = offered_position.government_position
                # Student council name
                student_council \
                    = "CENTRAL" if not government_position.college \
                    else government_position.college.name
                # Position name
                position_name = f'{student_council} - ' \
                                f'{offered_position.government_position.name}'

                # Candidate name
                candidate = winning_candidate.candidate
                candidate_name = f'{candidate.first_name} ' \
                    f'{candidate.last_name}'

                winning_candidate = models.ElectionSeasonWinningCandidate(
                    election_season=election_season,
                    running_candidate=winning_candidate,
                    position_name=position_name,
                    ballot_number=winning_candidate.ballot_number,
                    candidate_name=candidate_name)
                winners.append(winning_candidate)

        return winners

    def conclude_season_view(self, request, pk):
        election_season = (models.ElectionSeason.objects.filter(pk=pk)
                           .prefetch_related('ballot_set',
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
        # Get the winners
        winners = self.get_winners(election_season, tally)

        # Save the tally and winners
        for running_candidate in tally.values():
            running_candidate.save()
        for winning_candidate in winners:
            winning_candidate.save()

        messages.add_message(request, messages.SUCCESS,
                             f'Election Season {election_season} has been concluded.')
        return redirect(reverse('admin:elections_electionseason_changelist'))

    def season_statistics_view(self, request, pk):
        # TODO: Implement
        return JsonResponse({'helo': 'helo'})
