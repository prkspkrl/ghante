from django.conf import settings
from django.db import models


class Job(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('open', 'Open'),
        ('assigned', 'Assigned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    CATEGORY_CHOICES = [
        ('furniture-assembly', 'Furniture Assembly'),
        ('wall-mounting', 'Wall Mounting'),
        ('moving', 'Moving Help'),
        ('cleaning', 'Cleaning'),
        ('painting', 'Painting'),
        ('electrical', 'Electrical'),
        ('plumbing', 'Plumbing'),
        ('gardening', 'Gardening'),
        ('home-repairs', 'Home Repairs'),
        ('other', 'Other'),
    ]

    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='jobs_posted',
        null=True, blank=True
    )
    title = models.CharField(max_length=160)
    description = models.TextField(blank=True, default='')
    category = models.CharField(max_length=40, choices=CATEGORY_CHOICES, default='other')
    address = models.CharField(max_length=250, blank=True, default='')
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    budget = models.PositiveIntegerField(default=0)
    hours_needed = models.PositiveIntegerField(default=1, help_text='Estimated hours needed')
    preferred_date = models.DateField(null=True, blank=True)
    workers_needed = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    started_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class JobPhoto(models.Model):
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='photos')
    image = models.ImageField(upload_to='job_photos/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Photo for {self.job.title}'


class JobApplication(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]

    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='applications')
    worker = models.ForeignKey('profiles.WorkerProfile', on_delete=models.CASCADE, related_name='job_applications')
    message = models.TextField(blank=True, default='')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('job', 'worker')

    def __str__(self):
        return f'{self.worker.name} -> {self.job.title}'
