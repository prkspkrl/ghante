from django.contrib import admin

from .models import CustomerAccount, UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'full_name',
        'role',
        'phone_number',
        'is_customer',
        'is_worker',
        'is_admin',
        'is_verified',
        'email_verified',
        'phone_verified',
        'created_at',
    )
    list_filter = ('role', 'is_customer', 'is_worker', 'is_admin', 'is_verified', 'email_verified', 'phone_verified', 'created_at')
    search_fields = ('user__username', 'user__email', 'full_name', 'phone_number')


@admin.register(CustomerAccount)
class CustomerAccountAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'phone', 'created_at')
    search_fields = ('full_name', 'email', 'phone')
