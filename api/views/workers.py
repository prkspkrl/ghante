import math
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from profiles.models import WorkerProfile, Booking, Favorite
from profiles.serializers import WorkerProfileSerializer, WorkerProfileListSerializer, BookingSerializer

ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/jpg']
MAX_SIZE = 1 * 1024 * 1024


def _validate_image(file, field_name):
    if not file:
        return None
    if file.content_type not in ALLOWED_TYPES:
        return f'{field_name} must be JPG or PNG format.'
    if file.size > MAX_SIZE:
        return f'{field_name} must be within 1 MB.'
    return None


def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (math.sin(d_lat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(d_lon / 2) ** 2)
    return R * 2 * math.asin(math.sqrt(a))


class WorkerListView(generics.ListAPIView):
    serializer_class = WorkerProfileListSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        qs = WorkerProfile.objects.filter(is_available=True).select_related('user', 'user__profile')
        p = self.request.query_params

        if p.get('category'):
            qs = qs.filter(category=p['category'])
        if p.get('search'):
            qs = qs.filter(
                models.Q(name__icontains=p['search']) |
                models.Q(skill__icontains=p['search']) |
                models.Q(bio__icontains=p['search']) |
                models.Q(location__icontains=p['search']) |
                models.Q(languages__icontains=p['search'])
            )
        if p.get('min_rate'):
            qs = qs.filter(hourly_rate__gte=int(p['min_rate']))
        if p.get('max_rate'):
            qs = qs.filter(hourly_rate__lte=int(p['max_rate']))
        if p.get('min_rating'):
            qs = qs.filter(rating__gte=float(p['min_rating']))
        if p.get('availability'):
            qs = qs.filter(availability=p['availability'])
        if p.get('experience'):
            qs = qs.filter(experience=p['experience'])
        if p.get('is_verified'):
            qs = qs.filter(is_verified=p['is_verified'] == 'true')

        lat = p.get('lat')
        lng = p.get('lng')
        distance_km = p.get('distance_km')
        if lat and lng and distance_km:
            center_lat = float(lat)
            center_lng = float(lng)
            max_dist = float(distance_km)
            candidates = []
            for w in qs:
                if w.latitude and w.longitude:
                    if haversine(center_lat, center_lng, w.latitude, w.longitude) <= max_dist:
                        candidates.append(w.pk)
            qs = qs.filter(pk__in=candidates)

        sort = p.get('sort', '-rating')
        if sort in ['rating', '-rating', 'hourly_rate', '-hourly_rate', 'jobs_count', '-jobs_count', 'created_at', '-created_at']:
            qs = qs.order_by(sort)

        return qs


class WorkerDetailView(generics.RetrieveAPIView):
    serializer_class = WorkerProfileSerializer
    permission_classes = [AllowAny]
    queryset = WorkerProfile.objects.select_related('user', 'user__profile')


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def worker_create_or_update(request):
    user = request.user
    data = request.data
    photo = request.FILES.get('photo')
    citizenship_photo = request.FILES.get('citizenship_photo')

    err = _validate_image(photo, 'Profile photo')
    if err:
        return Response({'error': err}, status=status.HTTP_400_BAD_REQUEST)
    err = _validate_image(citizenship_photo, 'Citizenship photo')
    if err:
        return Response({'error': err}, status=status.HTTP_400_BAD_REQUEST)

    name = data.get('name', '').strip()
    skill = data.get('skill', '').strip()
    if not name or not skill:
        return Response({'error': 'name and skill are required'}, status=status.HTTP_400_BAD_REQUEST)

    defaults = {
        'name': name,
        'skill': skill,
        'bio': data.get('bio', ''),
        'hourly_rate': int(data.get('hourly_rate', 0)),
        'location': data.get('location', ''),
        'latitude': float(data['latitude']) if 'latitude' in data and data['latitude'] else None,
        'longitude': float(data['longitude']) if 'longitude' in data and data['longitude'] else None,
        'category': data.get('category', 'other'),
        'languages': data.get('languages', ''),
        'experience': data.get('experience', ''),
        'availability': data.get('availability', ''),
        'is_available': data.get('is_available', 'true') == 'true',
    }

    obj, created = WorkerProfile.objects.update_or_create(
        user=user, defaults=defaults,
    )

    if photo:
        obj.photo = photo
    if citizenship_photo:
        obj.citizenship_photo = citizenship_photo
        obj.is_verified = False
    obj.save()

    # Update user profile role
    if hasattr(user, 'profile'):
        user.profile.is_worker = True
        user.profile.role = 'worker'
        user.profile.save(update_fields=['is_worker', 'role'])

    return Response(
        WorkerProfileSerializer(obj, context={'request': request}).data,
        status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def worker_toggle_availability(request):
    user = request.user
    if not hasattr(user, 'worker_profile'):
        return Response({'error': 'No worker profile'}, status=status.HTTP_404_NOT_FOUND)
    wp = user.worker_profile
    wp.is_available = not wp.is_available
    wp.save(update_fields=['is_available'])
    return Response({'is_available': wp.is_available})


class BookingListCreateView(generics.ListCreateAPIView):
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        email = user.email
        qs = Booking.objects.filter(customer_email=email)
        if hasattr(user, 'worker_profile'):
            qs = qs | Booking.objects.filter(worker=user.worker_profile)
        return qs.select_related('worker').order_by('-created_at')

    def perform_create(self, serializer):
        user = self.request.user
        data = serializer.validated_data
        data['customer_name'] = data.get('customer_name', user.profile.full_name or user.username)
        data['customer_email'] = user.email
        serializer.save(**data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def respond_booking(request, pk):
    booking = Booking.objects.filter(pk=pk).first()
    if not booking:
        return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

    user = request.user
    if not hasattr(user, 'worker_profile') or booking.worker != user.worker_profile:
        return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)

    action = request.data.get('action')
    if action not in ['accept', 'reject', 'complete']:
        return Response({'error': 'Action must be accept, reject, or complete'}, status=status.HTTP_400_BAD_REQUEST)

    booking.status = action if action != 'complete' else 'completed'
    booking.response_message = request.data.get('message', '')
    booking.save()

    try:
        from notifications.services import notify_booking_status
        notify_booking_status(booking, booking.status)
    except Exception:
        pass

    return Response({'message': f'Booking {booking.status}'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cancel_booking(request, pk):
    booking = Booking.objects.filter(pk=pk, customer_email=request.user.email).first()
    if not booking:
        return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

    if booking.status != 'pending':
        return Response({'error': 'Only pending bookings can be cancelled'}, status=status.HTTP_400_BAD_REQUEST)

    booking.status = 'cancelled'
    booking.save()
    return Response({'message': 'Booking cancelled'})
