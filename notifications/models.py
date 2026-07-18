from django.conf import settings
from django.db import models


class Notification(models.Model):
    TYPE_CHOICES = [
        ('job', 'New Job'),
        ('application', 'Application'),
        ('accepted', 'Accepted'),
        ('message', 'New Message'),
        ('review', 'Review'),
        ('verification', 'Verification'),
        ('booking', 'Booking'),
    ]

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='notifications', null=True, blank=True,
    )
    recipient_email = models.EmailField(default='', blank=True)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='triggered_notifications',
    )
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='booking')
    title = models.CharField(max_length=160)
    message = models.TextField()
    target_url = models.CharField(max_length=255, blank=True, default='')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title
