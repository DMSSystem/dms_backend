from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny

from models.review import Review, HelpfulReview
from models.material import LearningMaterial
from serializers.review_serializers import (
    ReviewSerializer, ReviewCreateSerializer, ReviewUpdateSerializer,
    HelpfulReviewSerializer, HelpfulReviewToggleSerializer
)


class ReviewViewSet(viewsets.ModelViewSet):
    """ViewSet for material reviews"""
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['rating', 'helpful_count', 'created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        material_id = self.request.query_params.get('material_id')
        if material_id:
            return Review.objects.filter(material_id=material_id)
        return Review.objects.all()

    def get_serializer_class(self):
        if self.action == 'create':
            return ReviewCreateSerializer
        elif self.action == 'update' or self.action == 'partial_update':
            return ReviewUpdateSerializer
        return ReviewSerializer

    def perform_create(self, serializer):
        """Create review with current user as reviewer"""
        material = LearningMaterial.objects.get(pk=serializer.validated_data['material'].id)
        
        # Check if user has downloaded this material
        is_verified = material.downloads_record.filter(user=self.request.user).exists()
        
        serializer.save(reviewer=self.request.user, is_verified_purchase=is_verified)
        
        # Update material rating
        update_material_rating(material)

    def perform_update(self, serializer):
        """Update review and recalculate rating"""
        review = self.get_object()
        serializer.save()
        update_material_rating(review.material)

    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def material_reviews(self, request):
        """Get all reviews for a material"""
        material_id = request.query_params.get('material_id')
        if not material_id:
            return Response(
                {'error': 'material_id parameter required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        reviews = Review.objects.filter(material_id=material_id)
        serializer = self.get_serializer(reviews, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def my_reviews(self, request):
        """Get current user's reviews"""
        reviews = Review.objects.filter(reviewer=request.user)
        serializer = self.get_serializer(reviews, many=True)
        return Response(serializer.data)


class HelpfulReviewViewSet(viewsets.ViewSet):
    """ViewSet for marking reviews as helpful/unhelpful"""
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'])
    def toggle_helpful(self, request):
        """Toggle helpful/unhelpful vote on a review"""
        serializer = HelpfulReviewToggleSerializer(data=request.data)
        if serializer.is_valid():
            review_id = serializer.validated_data['review_id']
            is_helpful = serializer.validated_data['is_helpful']
            
            review = Review.objects.get(pk=review_id)
            
            # Check if user already voted
            try:
                vote = HelpfulReview.objects.get(review=review, user=request.user)
                # Update existing vote
                if vote.is_helpful != is_helpful:
                    if vote.is_helpful:
                        review.helpful_count -= 1
                    else:
                        review.unhelpful_count -= 1
                    
                    vote.is_helpful = is_helpful
                    vote.save()
                    
                    if is_helpful:
                        review.helpful_count += 1
                    else:
                        review.unhelpful_count += 1
                    review.save()
                else:
                    # Remove vote if same
                    if vote.is_helpful:
                        review.helpful_count -= 1
                    else:
                        review.unhelpful_count -= 1
                    vote.delete()
                    review.save()
            except HelpfulReview.DoesNotExist:
                # Create new vote
                HelpfulReview.objects.create(
                    review=review,
                    user=request.user,
                    is_helpful=is_helpful
                )
                
                if is_helpful:
                    review.helpful_count += 1
                else:
                    review.unhelpful_count += 1
                review.save()
            
            return Response({
                'helpful_count': review.helpful_count,
                'unhelpful_count': review.unhelpful_count
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


def update_material_rating(material):
    """Recalculate material rating based on reviews"""
    from django.db.models import Avg
    
    avg_rating = Review.objects.filter(material=material).aggregate(
        avg_rating=Avg('rating')
    )['avg_rating']
    
    if avg_rating:
        material.rating = round(avg_rating, 2)
        material.total_reviews = Review.objects.filter(material=material).count()
    else:
        material.rating = 0
        material.total_reviews = 0
    
    material.save(update_fields=['rating', 'total_reviews'])
