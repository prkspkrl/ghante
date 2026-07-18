from django.contrib import admin

from .models import ChatMessage, TypingStatus


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('sender_name', 'worker', 'message_type', 'sent_at', 'is_read')
    list_filter = ('message_type', 'is_read', 'sent_at')
    search_fields = ('sender_name', 'worker__name', 'message')


@admin.register(TypingStatus)
class TypingStatusAdmin(admin.ModelAdmin):
    list_display = ('user', 'worker', 'is_typing', 'updated_at')
    list_filter = ('is_typing',)
