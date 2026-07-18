from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from reviews.models import Review
from reviews.serializers import ReviewSerializer


class ReviewListCreateView(generics.ListCreateAPIView):
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Review.objects.filter(reviewer=self.request.user).select_related('worker', 'job').order_by('-created_at')

    def perform_create(self, serializer):
        user = self.request.user
        data = serializer.validated_data
        review_type = data.get('review_type', 'customer_to_worker')
        worker = data.get('worker')
        job = data.get('job')

        # Validate job exists and is completed
        if job:
            if review_type == 'customer_to_worker':
                if job.customer != user:
                    from rest_framework.exceptions import ValidationError
                    raise ValidationError('You can only review workers from your own jobs.')
                if job.status not in ['assigned', 'in_progress', 'completed']:
                    from rest_framework.exceptions import ValidationError
                    raise ValidationError('Job must be at least assigned to leave a review.')
            elif review_type == 'worker_to_customer':
                if not hasattr(user, 'worker_profile') or job.status != 'completed':
                    from rest_framework.exceptions import ValidationError
                    raise ValidationError('Job must be completed for worker-to-customer review.')

        # Prevent duplicate reviews
        if worker and job:
            existing = Review.objects.filter(
                reviewer=user, worker=worker, job=job, review_type=review_type,
            ).exists()
            if existing:
                from rest_framework.exceptions import ValidationError
                raise ValidationError('You have already reviewed this worker for this job.')

        review = serializer.save(reviewer=user)

        # Update worker's average rating
        if review.worker:
            from django.db.models import Avg
            avg = Review.objects.filter(worker=review.worker).aggregate(avg_rating=Avg('rating'))['avg_rating']
            if avg:
                review.worker.rating = round(avg, 1)
                review.worker.save()


class WorkerReviewsPublicView(generics.ListAPIView):
    serializer_class = ReviewSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        from profiles.models import WorkerProfile
        worker = WorkerProfile.objects.filter(pk=self.kwargs['worker_id']).first()
        if not worker:
            return Review.objects.none()
        return Review.objects.filter(worker=worker).select_related('reviewer').order_by('-created_at')
