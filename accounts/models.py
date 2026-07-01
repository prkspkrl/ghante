from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('customer', 'Customer'),
        ('worker', 'Worker'),
        ('admin', 'Admin'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    full_name = models.CharField(max_length=120, blank=True, default='')
    phone_number = models.CharField(max_length=30, blank=True, db_column='phone')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='customer')
    is_customer = models.BooleanField(default=True)
    is_worker = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    email_verified = models.BooleanField(default=False)
    phone_verified = models.BooleanField(default=False)
    phone_verification_code = models.CharField(max_length=10, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.username} ({self.get_role_display()})'


class CustomerAccount(models.Model):
    full_name = models.CharField(max_length=120)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=30, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.full_name
