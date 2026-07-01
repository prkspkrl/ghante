from django.db import models



class SiteSetting(models.Model):
    name = models.CharField(max_length=120)
    value = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
