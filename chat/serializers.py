from rest_framework import serializers
from chat.models import ChatMessage


class ChatMessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = ChatMessage
        fields = [
            'id', 'worker', 'sender', 'sender_name', 'message',
            'message_type', 'image', 'image_url', 'sent_at',
            'is_read', 'read_at',
        ]
        read_only_fields = ['id', 'sender', 'sent_at', 'is_read', 'read_at']

    def get_sender_name(self, obj):
        if obj.sender:
            if hasattr(obj.sender, 'profile'):
                return obj.sender.profile.full_name or obj.sender.username
            return obj.sender.username
        return obj.sender_name

    def get_image_url(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None


class ConversationSerializer(serializers.Serializer):
    worker_id = serializers.IntegerField()
    worker_name = serializers.CharField()
    worker_photo_url = serializers.URLField(allow_null=True, required=False)
    last_message = serializers.CharField()
    last_message_time = serializers.DateTimeField()
    unread_count = serializers.IntegerField()
