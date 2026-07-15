from django.contrib import admin

from .models import Booking, WorkerProfile


@admin.register(WorkerProfile)
class WorkerProfileAdmin(admin.ModelAdmin):
    list_display = ('name', 'skill', 'hourly_rate', 'location', 'is_verified', 'rating', 'jobs_count', 'is_available')
    list_filter = ('is_available', 'is_verified', 'skill')
    search_fields = ('name', 'skill', 'location')


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('customer_name', 'worker', 'preferred_date', 'status', 'created_at')
    list_filter = ('status', 'preferred_date')
    search_fields = ('customer_name', 'worker__name')
