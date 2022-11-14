from django.contrib import admin
from django.utils.html import mark_safe

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
    list_display = ('academic_year', 'status', 'initiated_on', 'concluded_on', 'manage', 'override',)

    fields = ('academic_year',)
    inlines = [OfferedPositionTabularInline, RunningCandidateTabularInline,]

    # TODO: Add views for initiating, concluding, and overriding

    @admin.display()
    def manage(self, obj):
        if not obj.status:
            return mark_safe(f'<a href="{obj.id}/initiate/">Initiate</a>')
        elif obj.status == "INITIATED":
            return mark_safe(f'<a href="{obj.id}/conclude/">Conclude</a>')
        else:
            return "N/A"

    @admin.display()
    def override(self, obj):
        if obj.status == "CONCLUDED":
            return mark_safe(f'<a href="{obj.id}/override/">Override</a>')
        else:
            return "N/A"
