from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from .models import SearchQuery, SiteSetting


@admin.register(SiteSetting)
class SiteSettingAdmin(admin.ModelAdmin):
    list_display = ('name', 'updated_at')
    search_fields = ('name', 'value')


@admin.register(SearchQuery)
class SearchQueryAdmin(admin.ModelAdmin):
    list_display = ('keyword', 'user', 'results_count', 'created_at')
    search_fields = ('keyword',)
    list_filter = ('created_at',)
    readonly_fields = ('keyword', 'user', 'results_count', 'created_at')

    def changelist_view(self, request, extra_context=None):
        analytics_url = reverse('search_analytics')
        download_url = reverse('search_analytics_csv')
        extra_context = extra_context or {}
        extra_context['analytics_link'] = analytics_url
        extra_context['download_link'] = download_url
        return super().changelist_view(request, extra_context=extra_context)
