from django.contrib import admin

from .models import ChatMessage


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('sender_name', 'recipient_name', 'sent_at', 'is_read')
    list_filter = ('is_read', 'sent_at')
    search_fields = ('sender_name', 'recipient_name', 'message')
