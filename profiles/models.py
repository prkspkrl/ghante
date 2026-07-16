from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class Booking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    worker = models.ForeignKey('WorkerProfile', on_delete=models.CASCADE, related_name='bookings')
    customer_name = models.CharField(max_length=120)
    customer_email = models.EmailField()
    customer_phone = models.CharField(max_length=30, blank=True)
    preferred_date = models.DateField()
    preferred_time = models.TimeField(blank=True, null=True)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    response_message = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f'{self.customer_name} -> {self.worker.name} ({self.status})'


class WorkerProfile(models.Model):
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

    AVAILABILITY_CHOICES = [
        ('weekdays', 'Weekdays'),
        ('weekends', 'Weekends'),
        ('flexible', 'Flexible'),
        ('mornings', 'Mornings'),
        ('afternoons', 'Afternoons'),
        ('evenings', 'Evenings'),
    ]

    EXPERIENCE_CHOICES = [
        ('0-1', 'Less than 1 year'),
        ('1-3', '1-3 years'),
        ('3-5', '3-5 years'),
        ('5-10', '5-10 years'),
        ('10+', '10+ years'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True, related_name='worker_profile')
    name = models.CharField(max_length=120)
    skill = models.CharField(max_length=120)
    bio = models.TextField(blank=True, default='')
    hourly_rate = models.PositiveIntegerField(default=0)
    location = models.CharField(max_length=120, blank=True)
    category = models.CharField(max_length=40, choices=CATEGORY_CHOICES, default='other')
    languages = models.CharField(max_length=200, blank=True, default='', help_text='Comma-separated, e.g. English, Nepali, Hindi')
    experience = models.CharField(max_length=20, choices=EXPERIENCE_CHOICES, blank=True, default='')
    availability = models.CharField(max_length=20, choices=AVAILABILITY_CHOICES, blank=True, default='')
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
