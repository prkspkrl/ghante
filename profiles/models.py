from django.db import models


class WorkerProfile(models.Model):
    name = models.CharField(max_length=120)
    skill = models.CharField(max_length=120)
    hourly_rate = models.PositiveIntegerField(default=0)
    location = models.CharField(max_length=120, blank=True)
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.name} - {self.skill}'
