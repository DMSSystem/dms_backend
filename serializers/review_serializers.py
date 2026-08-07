from rest_framework import serializers
from models.review import Review, HelpfulReview
from .user_serializers import UserSerializer

class ReviewSerializer(serializers.ModelSerializer):
    reviewer = UserSerializer(read_only=True)
    helpful_votes = serializers.SerializerMethodField()
    
    class Meta:
        model = Review
        fields = [
            'id', 'material', 'reviewer', 'rating', 'title', 'comment',
            'helpful_count', 'unhelpful_count', 'is_verified_purchase',
            'helpful_votes', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'reviewer', 'helpful_count', 'unhelpful_count',
            'is_verified_purchase', 'created_at', 'updated_at'
        ]

    def get_helpful_votes(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                vote = HelpfulReview.objects.get(review=obj, user=request.user)
                return vote.is_helpful
            except HelpfulReview.DoesNotExist:
                return None
        return None


class ReviewCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating reviews"""
    class Meta:
        model = Review
        fields = ['material', 'rating', 'title', 'comment']

    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value


class ReviewUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating reviews"""
    class Meta:
        model = Review
        fields = ['rating', 'title', 'comment']

    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value


class HelpfulReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = HelpfulReview
        fields = ['id', 'review', 'user', 'is_helpful', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']


class HelpfulReviewToggleSerializer(serializers.Serializer):
    """Serializer for toggling helpful/unhelpful votes"""
    review_id = serializers.IntegerField()
    is_helpful = serializers.BooleanField()
