from rest_framework import serializers
from notifications.models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            'id', 'notification_type', 'title', 'message',
            'target_url', 'is_read', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']
