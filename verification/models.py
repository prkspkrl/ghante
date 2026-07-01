from django.db import models



class VerificationRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    applicant_name = models.CharField(max_length=120)
    document_type = models.CharField(max_length=80)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.applicant_name} - {self.status}'
