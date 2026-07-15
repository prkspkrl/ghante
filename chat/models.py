from django.contrib.auth.models import User
from django.db import models


class ChatMessage(models.Model):
    worker = models.ForeignKey('profiles.WorkerProfile', on_delete=models.CASCADE, related_name='chat_messages')
    sender = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='sent_messages')
    sender_name = models.CharField(max_length=120)
    message = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['sent_at']

    def __str__(self):
        return f'{self.sender_name} -> {self.worker.name}'
