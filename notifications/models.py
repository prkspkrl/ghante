from django.db import models



class Notification(models.Model):
    recipient_email = models.EmailField(default='', blank=True)
    title = models.CharField(max_length=160)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
