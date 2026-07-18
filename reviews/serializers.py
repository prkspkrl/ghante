from rest_framework import serializers
from reviews.models import Review


class ReviewSerializer(serializers.ModelSerializer):
    reviewer_name = serializers.SerializerMethodField()
    worker_name = serializers.CharField(source='worker.name', read_only=True)

    class Meta:
        model = Review
        fields = [
            'id', 'reviewer', 'reviewer_name', 'worker', 'worker_name',
            'job', 'review_type', 'rating', 'comment', 'created_at',
        ]
        read_only_fields = ['id', 'reviewer', 'created_at']

    def get_reviewer_name(self, obj):
        if obj.reviewer:
            if hasattr(obj.reviewer, 'profile'):
                return obj.reviewer.profile.full_name or obj.reviewer.username
            return obj.reviewer.username
        return 'Anonymous'

    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError('Rating must be between 1 and 5.')
        return value
