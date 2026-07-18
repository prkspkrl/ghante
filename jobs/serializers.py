from rest_framework import serializers
from jobs.models import Job, JobPhoto, JobApplication


class JobPhotoSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = JobPhoto
        fields = ['id', 'image', 'image_url', 'uploaded_at']
        read_only_fields = ['id', 'uploaded_at']

    def get_image_url(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None


class JobApplicationSerializer(serializers.ModelSerializer):
    worker_name = serializers.CharField(source='worker.name', read_only=True)
    worker_rating = serializers.FloatField(source='worker.rating', read_only=True)
    worker_category = serializers.CharField(source='worker.category', read_only=True)

    class Meta:
        model = JobApplication
        fields = [
            'id', 'job', 'worker', 'worker_name', 'worker_rating',
            'worker_category', 'message', 'status', 'created_at',
        ]
        read_only_fields = ['id', 'status', 'created_at']


class JobSerializer(serializers.ModelSerializer):
    photos = JobPhotoSerializer(many=True, read_only=True)
    application_count = serializers.SerializerMethodField()
    customer_name = serializers.SerializerMethodField()

    class Meta:
        model = Job
        fields = [
            'id', 'customer', 'customer_name', 'title', 'description',
            'category', 'address', 'latitude', 'longitude',
            'budget', 'hours_needed', 'preferred_date', 'workers_needed',
            'status', 'started_at', 'created_at', 'updated_at',
            'photos', 'application_count',
        ]
        read_only_fields = ['id', 'customer', 'status', 'started_at', 'created_at', 'updated_at']

    def get_application_count(self, obj):
        return obj.applications.count()

    def get_customer_name(self, obj):
        if obj.customer:
            if hasattr(obj.customer, 'profile'):
                return obj.customer.profile.full_name or obj.customer.username
            return obj.customer.username
        return None


class JobListSerializer(serializers.ModelSerializer):
    application_count = serializers.SerializerMethodField()

    class Meta:
        model = Job
        fields = [
            'id', 'title', 'category', 'address', 'budget',
            'hours_needed', 'preferred_date', 'workers_needed',
            'status', 'created_at', 'application_count',
        ]

    def get_application_count(self, obj):
        return obj.applications.count()
