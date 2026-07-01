from django.contrib import admin

from .models import WorkerProfile


@admin.register(WorkerProfile)
class WorkerProfileAdmin(admin.ModelAdmin):
    list_display = ('name', 'skill', 'hourly_rate', 'location', 'is_available')
    list_filter = ('is_available', 'skill')
    search_fields = ('name', 'skill', 'location')
