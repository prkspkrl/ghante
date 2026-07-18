import math
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from jobs.models import Job, JobApplication, JobPhoto
from jobs.serializers import JobSerializer, JobListSerializer, JobApplicationSerializer, JobPhotoSerializer
from api.permissions import IsCustomer, IsOwnerOrReadOnly


class JobListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return JobListSerializer
        return JobSerializer

    def get_queryset(self):
        return Job.objects.filter(customer=self.request.user).select_related('customer').order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(customer=self.request.user)


class JobDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = JobSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

    def get_queryset(self):
        return Job.objects.filter(customer=self.request.user).select_related('customer')

    def perform_destroy(self, instance):
        if instance.status in ['draft', 'open']:
            instance.delete()
        else:
            instance.status = 'cancelled'
            instance.save()


class JobApplicationsView(generics.ListAPIView):
    serializer_class = JobApplicationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        job = Job.objects.filter(pk=self.kwargs['pk'], customer=self.request.user).first()
        if not job:
            return JobApplication.objects.none()
        return JobApplication.objects.filter(job=job).select_related('worker', 'worker__user')


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def apply_to_job(request, pk):
    job = Job.objects.filter(pk=pk, status='open').first()
    if not job:
        return Response({'error': 'Job not found or not open'}, status=status.HTTP_404_NOT_FOUND)

    worker = request.user.worker_profile if hasattr(request.user, 'worker_profile') else None
    if not worker:
        return Response({'error': 'You do not have a worker profile'}, status=status.HTTP_400_BAD_REQUEST)

    if JobApplication.objects.filter(job=job, worker=worker).exists():
        return Response({'error': 'Already applied'}, status=status.HTTP_400_BAD_REQUEST)

    application = JobApplication.objects.create(
        job=job, worker=worker, message=request.data.get('message', '')
    )
    return Response(JobApplicationSerializer(application).data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def accept_application(request, pk):
    application = JobApplication.objects.select_related('job', 'worker').filter(pk=pk).first()
    if not application:
        return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
    if application.job.customer != request.user:
        return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)

    application.status = 'accepted'
    application.save()
    application.job.status = 'assigned'
    application.job.save()
    JobApplication.objects.filter(job=application.job).exclude(pk=application.pk).update(status='rejected')
    return Response({'message': 'Application accepted'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reject_application(request, pk):
    application = JobApplication.objects.filter(pk=pk).first()
    if not application:
        return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
    if application.job.customer != request.user:
        return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)

    application.status = 'rejected'
    application.save()
    return Response({'message': 'Application rejected'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_job_status(request, pk):
    job = Job.objects.filter(pk=pk, customer=request.user).first()
    if not job:
        return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

    new_status = request.data.get('status')
    valid_transitions = {
        'open': ['cancelled'],
        'assigned': ['in_progress', 'cancelled'],
        'in_progress': ['completed', 'cancelled'],
    }
    allowed = valid_transitions.get(job.status, [])
    if new_status not in allowed:
        return Response({'error': f'Cannot transition from {job.status} to {new_status}'}, status=status.HTTP_400_BAD_REQUEST)

    job.status = new_status
    job.save()
    return Response({'message': f'Status updated to {new_status}'})


class JobBrowseView(generics.ListAPIView):
    serializer_class = JobListSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        qs = Job.objects.filter(status='open').select_related('customer')
        p = self.request.query_params

        if p.get('category'):
            qs = qs.filter(category=p['category'])
        if p.get('search'):
            qs = qs.filter(title__icontains=p['search'])
        if p.get('min_budget'):
            qs = qs.filter(budget__gte=int(p['min_budget']))
        if p.get('max_budget'):
            qs = qs.filter(budget__lte=int(p['max_budget']))

        lat = p.get('lat')
        lng = p.get('lng')
        distance_km = p.get('distance_km')
        if lat and lng and distance_km:
            center_lat = float(lat)
            center_lng = float(lng)
            max_dist = float(distance_km)
            candidates = []
            for j in qs:
                if j.latitude and j.longitude:
                    if haversine(center_lat, center_lng, j.latitude, j.longitude) <= max_dist:
                        candidates.append(j.pk)
            qs = qs.filter(pk__in=candidates)

        sort = p.get('sort', '-created_at')
        if sort in ['budget', '-budget', 'created_at', '-created_at', 'hours_needed', '-hours_needed']:
            qs = qs.order_by(sort)

        return qs


def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (math.sin(d_lat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(d_lon / 2) ** 2)
    return R * 2 * math.asin(math.sqrt(a))


class JobPhotoUploadView(generics.CreateAPIView):
    serializer_class = JobPhotoSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        job = Job.objects.filter(pk=self.kwargs['pk'], customer=self.request.user).first()
        if not job:
            from rest_framework.exceptions import NotFound
            raise NotFound
        serializer.save(job=job)
