from django.contrib import admin
from django.utils.html import mark_safe
from django.urls import path
from django.http import JsonResponse
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone

import threading

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


class OfferedPositionTabularInline(admin.TabularInline):
    model = models.OfferedPosition
    extra = 0
    min_num = 1


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

    def tally_results(self, pk):
        election_season \
            = (models.ElectionSeason.objects.filter(pk=pk)
               .prefetch_related(
                'offeredposition_set',
                'offeredposition_set__government_position',
                'runningcandidate_set',
                'runningcandidate_set__government_position',
                'runningcandidate_set__candidate',
                'ballot_set',
                'ballot_set__voted_candidates')[0])

        # Have a dict store the tallied results where:
        # key = running candidate ID
        # value = vote count
        results = {running_candidate.id: 0
                   for running_candidate
                   in election_season.runningcandidate_set.all()}

        # Go through each ballot's voted candidates, add to tally
        for ballot in election_season.ballot_set.all():
            for voted_candidate in ballot.voted_candidates.all():
                results[voted_candidate.id] += 1

        # Now determine the winners for each position
        for offered_position in election_season.offeredposition_set.all():
            # Get all candidates running for this position
            running_candidates_for_pos \
                = election_season.runningcandidate_set.filter(
                    government_position=offered_position.government_position)

            # Now determine the winning candidate(s) for this position
            # by counterchecking with the tallied results (results dict)
            winning_candidates = []
            for running_candidate in running_candidates_for_pos:
                # Add to list if either:
                # - list is still empty
                # - candidate is a tie with the current contents
                if len(winning_candidates) == 0 \
                    or results[running_candidate.id] \
                        == results[winning_candidates[0].id]:
                    winning_candidates.append(running_candidate)
                # Overwrite the list if candidate has greater votes
                elif results[running_candidate.id] \
                        > results[winning_candidates[0].id]:
                    winning_candidates.clear()
                    winning_candidates.append(running_candidate)

                # Set the vote count for this object then save
                running_candidate.tallied_votes = results[running_candidate.id]
                running_candidate.save()

                # Save the winning candidate(s) on the summary table
                for winning_candidate in winning_candidates:
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

                    winning_candidate_record \
                        = models.ElectionSeasonWinningCandidate(
                            election_season=election_season,
                            running_candidate=winning_candidate,
                            position_name=position_name,
                            ballot_number=winning_candidate.ballot_number,
                            candidate_name=candidate_name)
                    winning_candidate_record.save()

        # Update status to concluded
        election_season.status = 'CONCLUDED'
        election_season.save()

    def conclude_season_view(self, request, pk):
        election_season = models.ElectionSeason.objects.get(pk=pk)

        # If status is not 'INITIATED', do nothing.
        if election_season.status != 'INITIATED':
            messages.add_message(
                request, messages.WARNING,
                f'Election Season {election_season}'
                ' cannot be concluded.')
            return redirect(
                reverse('admin:elections_electionseason_changelist'))

        election_season.status = 'CONCLUDING'
        election_season.concluded_on = timezone.now()
        election_season.save()

        tallying_thread = threading.Thread(
            target=self.tally_results, kwargs={'pk': pk})
        tallying_thread.setDaemon(True)
        tallying_thread.start()

        messages.add_message(request, messages.SUCCESS,
                             f'Election Season {election_season} has been concluded.')
        return redirect(reverse('admin:elections_electionseason_changelist'))

    def season_statistics_view(self, request, pk):
        # TODO: Implement
        return JsonResponse({'helo': 'helo'})
