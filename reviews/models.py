from django.db import models



class Review(models.Model):
    customer_name = models.CharField(max_length=120)
    worker_name = models.CharField(max_length=120)
    rating = models.PositiveSmallIntegerField(default=5)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.rating}/5 by {self.customer_name}'
