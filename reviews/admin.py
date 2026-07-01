from django.contrib import admin

from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('customer_name', 'worker_name', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('customer_name', 'worker_name', 'comment')
