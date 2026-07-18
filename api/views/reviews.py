from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
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
        review = serializer.save(reviewer=self.request.user)
        # Update worker's average rating
        if review.worker:
            from django.db.models import Avg
            avg = Review.objects.filter(worker=review.worker).aggregate(avg_rating=Avg('rating'))['avg_rating']
            if avg:
                review.worker.rating = round(avg, 1)
                review.worker.save()


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def worker_reviews(request, worker_id):
    from profiles.models import WorkerProfile
    worker = WorkerProfile.objects.filter(pk=worker_id).first()
    if not worker:
        return Response({'error': 'Worker not found'}, status=status.HTTP_404_NOT_FOUND)

    reviews = Review.objects.filter(worker=worker).select_related('reviewer').order_by('-created_at')
    serializer = ReviewSerializer(reviews, many=True, context={'request': request})
    return Response(serializer.data)
