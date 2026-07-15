from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class Booking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
    ]

    worker = models.ForeignKey('WorkerProfile', on_delete=models.CASCADE, related_name='bookings')
    customer_name = models.CharField(max_length=120)
    customer_email = models.EmailField()
    customer_phone = models.CharField(max_length=30, blank=True)
    preferred_date = models.DateField()
    preferred_time = models.TimeField(blank=True, null=True)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f'{self.customer_name} -> {self.worker.name} ({self.status})'


class WorkerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True, related_name='worker_profile')
    name = models.CharField(max_length=120)
    skill = models.CharField(max_length=120)
    bio = models.TextField(blank=True, default='')
    hourly_rate = models.PositiveIntegerField(default=0)
    location = models.CharField(max_length=120, blank=True)
    is_available = models.BooleanField(default=True)
    photo = models.ImageField(upload_to='worker_photos/', blank=True, null=True)
    citizenship_photo = models.ImageField(upload_to='worker_citizenship/', blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    rating = models.FloatField(default=4.5)
    jobs_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.name} - {self.skill}'
