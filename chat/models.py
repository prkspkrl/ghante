from django.contrib.auth.models import User
from django.db import models


class ChatMessage(models.Model):
    MESSAGE_TYPES = [
        ('text', 'Text'),
        ('image', 'Image'),
    ]

    worker = models.ForeignKey('profiles.WorkerProfile', on_delete=models.CASCADE, related_name='chat_messages')
    sender = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='sent_messages')
    sender_name = models.CharField(max_length=120)
    message = models.TextField(blank=True, default='')
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPES, default='text')
    image = models.ImageField(upload_to='chat_images/', blank=True, null=True)
    sent_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['sent_at']

    def __str__(self):
        return f'{self.sender_name} -> {self.worker.name}'


class TypingStatus(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='typing_status')
    worker = models.ForeignKey('profiles.WorkerProfile', on_delete=models.CASCADE, related_name='typing_users')
    is_typing = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'worker')

    def __str__(self):
        return f'{self.user.username} typing to {self.worker.name}'
