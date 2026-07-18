from django.conf import settings
from django.db import models


class Review(models.Model):
    TYPE_CHOICES = [
        ('customer_to_worker', 'Customer to Worker'),
        ('worker_to_customer', 'Worker to Customer'),
    ]

    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews_given',
        null=True, blank=True
    )
    worker = models.ForeignKey(
        'profiles.WorkerProfile', on_delete=models.CASCADE, related_name='reviews',
        null=True, blank=True
    )
    job = models.ForeignKey(
        'jobs.Job', on_delete=models.SET_NULL, null=True, blank=True, related_name='reviews'
    )
    review_type = models.CharField(max_length=30, choices=TYPE_CHOICES, default='customer_to_worker')
    rating = models.PositiveSmallIntegerField(default=5)
    comment = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        if self.review_type == 'customer_to_worker':
            return f'{self.reviewer.username} -> {self.worker.name} ({self.rating}/5)'
        return f'{self.reviewer.username} -> Customer ({self.rating}/5)'
