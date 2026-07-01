from django.db import models



class ChatMessage(models.Model):
    sender_name = models.CharField(max_length=120)
    recipient_name = models.CharField(max_length=120)
    message = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.sender_name} to {self.recipient_name}'
