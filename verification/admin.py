from django.contrib import admin

from .models import VerificationRequest


@admin.register(VerificationRequest)
class VerificationRequestAdmin(admin.ModelAdmin):
    list_display = ('applicant_name', 'document_type', 'status', 'submitted_at')
    list_filter = ('status', 'document_type')
    search_fields = ('applicant_name', 'document_type')
