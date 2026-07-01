from django.contrib import admin

from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('payer_name', 'amount', 'status', 'reference', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('payer_name', 'reference')
