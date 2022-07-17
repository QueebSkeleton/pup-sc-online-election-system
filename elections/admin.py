from django.contrib import admin

from . import models


@admin.register(models.College)
class CollegeAdmin(admin.ModelAdmin):
    list_display = ('name',)


@admin.register(models.PoliticalParty)
class PoliticalPartyAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_renewed',)


@admin.register(models.GovernmentPosition)
class GovernmentPositionAdmin(admin.ModelAdmin):
    list_display = ('name', 'description',)


@admin.register(models.Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = ('student_number', 'college', 'party', 'name',)

    @admin.display
    def name(self, obj):
        return "%s %s" % (obj.first_name, obj.last_name)


@admin.register(models.ElectionSeason)
class ElectionSeasonAdmin(admin.ModelAdmin):
    list_display = ('academic_year', 'status', 'initiated_on', 'concluded_on')
