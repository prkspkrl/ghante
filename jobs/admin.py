from django.contrib import admin

from .models import Job, JobApplication, JobPhoto


class JobPhotoInline(admin.TabularInline):
    model = JobPhoto
    extra = 0


class JobApplicationInline(admin.TabularInline):
    model = JobApplication
    extra = 0
    readonly_fields = ('worker', 'message', 'status', 'created_at')


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ('title', 'customer', 'category', 'budget', 'workers_needed', 'status', 'preferred_date', 'created_at')
    list_filter = ('status', 'category', 'preferred_date')
    search_fields = ('title', 'description', 'address', 'customer__username')
    inlines = [JobPhotoInline, JobApplicationInline]


@admin.register(JobPhoto)
class JobPhotoAdmin(admin.ModelAdmin):
    list_display = ('job', 'uploaded_at')


@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display = ('job', 'worker', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('job__title', 'worker__name')
