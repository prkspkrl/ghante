from rest_framework import serializers
from profiles.models import WorkerProfile, Booking, Favorite


class WorkerProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)
    review_count = serializers.SerializerMethodField()
    photo_url = serializers.SerializerMethodField()

    class Meta:
        model = WorkerProfile
        fields = [
            'id', 'username', 'email', 'name', 'skill', 'bio',
            'hourly_rate', 'location', 'latitude', 'longitude',
            'category', 'languages', 'experience', 'availability',
            'is_available', 'photo', 'photo_url', 'is_verified',
            'rating', 'jobs_count', 'created_at', 'updated_at',
            'review_count',
        ]
        read_only_fields = ['id', 'rating', 'jobs_count', 'created_at', 'updated_at']

    def get_review_count(self, obj):
        return obj.reviews.count()

    def get_photo_url(self, obj):
        if obj.photo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.photo.url)
            return obj.photo.url
        return None


class WorkerProfileListSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    review_count = serializers.SerializerMethodField()
    photo_url = serializers.SerializerMethodField()

    class Meta:
        model = WorkerProfile
        fields = [
            'id', 'username', 'name', 'skill', 'hourly_rate',
            'location', 'category', 'experience', 'availability',
            'is_available', 'photo_url', 'is_verified',
            'rating', 'jobs_count', 'review_count',
        ]

    def get_review_count(self, obj):
        return obj.reviews.count()

    def get_photo_url(self, obj):
        if obj.photo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.photo.url)
            return obj.photo.url
        return None


class BookingSerializer(serializers.ModelSerializer):
    worker_name = serializers.CharField(source='worker.name', read_only=True)
    worker_id = serializers.IntegerField(source='worker.pk', read_only=True)

    class Meta:
        model = Booking
        fields = [
            'id', 'worker', 'worker_id', 'worker_name',
            'customer_name', 'customer_email', 'customer_phone',
            'preferred_date', 'preferred_time', 'description',
            'status', 'response_message', 'created_at',
        ]
        read_only_fields = ['id', 'status', 'response_message', 'created_at']


class FavoriteSerializer(serializers.ModelSerializer):
    worker_detail = WorkerProfileListSerializer(source='worker', read_only=True)

    class Meta:
        model = Favorite
        fields = ['id', 'worker', 'worker_detail', 'created_at']
        read_only_fields = ['id', 'created_at']
