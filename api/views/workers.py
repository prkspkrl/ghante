import math
from rest_framework import generics, filters
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from profiles.models import WorkerProfile
from profiles.serializers import WorkerProfileSerializer, WorkerProfileListSerializer


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
            qs = qs.filter(name__icontains=p['search'])
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

        # Distance filter
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
