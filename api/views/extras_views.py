from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from models.extras import Favorite, Collection, CollectionItem, Notification
from models.material import LearningMaterial
from serializers.extras_serializers import (
    FavoriteSerializer, CollectionSerializer, CollectionCreateSerializer,
    NotificationSerializer, NotificationMarkReadSerializer
)


class FavoriteViewSet(viewsets.ViewSet):
    """ViewSet for favorite materials"""
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def list(self, request):
        """Get user's favorite materials"""
        favorites = Favorite.objects.filter(user=request.user).select_related('material')
        serializer = FavoriteSerializer(favorites, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def add_favorite(self, request):
        """Add material to favorites"""
        material_id = request.data.get('material_id')
        try:
            material = LearningMaterial.objects.get(pk=material_id, status='approved')
            favorite, created = Favorite.objects.get_or_create(
                user=request.user,
                material=material
            )
            if created:
                return Response(
                    {'message': 'Added to favorites'},
                    status=status.HTTP_201_CREATED
                )
            return Response(
                {'message': 'Already in favorites'},
                status=status.HTTP_200_OK
            )
        except LearningMaterial.DoesNotExist:
            return Response(
                {'error': 'Material not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['post'])
    def remove_favorite(self, request):
        """Remove material from favorites"""
        material_id = request.data.get('material_id')
        try:
            Favorite.objects.get(
                user=request.user,
                material_id=material_id
            ).delete()
            return Response({'message': 'Removed from favorites'})
        except Favorite.DoesNotExist:
            return Response(
                {'error': 'Favorite not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['get'])
    def check_favorite(self, request):
        """Check if material is favorited"""
        material_id = request.query_params.get('material_id')
        is_favorited = Favorite.objects.filter(
            user=request.user,
            material_id=material_id
        ).exists()
        return Response({'is_favorited': is_favorited})


class CollectionViewSet(viewsets.ModelViewSet):
    """ViewSet for collections"""
    permission_classes = [IsAuthenticated]
    serializer_class = CollectionSerializer

    def get_queryset(self):
        return Collection.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """Create collection for current user"""
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def add_material(self, request, pk=None):
        """Add material to collection"""
        collection = self.get_object()
        material_id = request.data.get('material_id')
        
        try:
            material = LearningMaterial.objects.get(pk=material_id, status='approved')
            
            # Get max order
            max_order = CollectionItem.objects.filter(
                collection=collection
            ).values_list('order', flat=True).order_by('-order').first() or 0
            
            item, created = CollectionItem.objects.get_or_create(
                collection=collection,
                material=material,
                defaults={'order': max_order + 1}
            )
            
            if created:
                return Response(
                    {'message': 'Material added to collection'},
                    status=status.HTTP_201_CREATED
                )
            return Response(
                {'message': 'Material already in collection'},
                status=status.HTTP_200_OK
            )
        except LearningMaterial.DoesNotExist:
            return Response(
                {'error': 'Material not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'])
    def remove_material(self, request, pk=None):
        """Remove material from collection"""
        collection = self.get_object()
        material_id = request.data.get('material_id')
        
        try:
            CollectionItem.objects.get(
                collection=collection,
                material_id=material_id
            ).delete()
            return Response({'message': 'Material removed from collection'})
        except CollectionItem.DoesNotExist:
            return Response(
                {'error': 'Item not found in collection'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['get'])
    def my_collections(self, request):
        """Get current user's collections"""
        collections = Collection.objects.filter(user=request.user)
        serializer = self.get_serializer(collections, many=True)
        return Response(serializer.data)


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for notifications"""
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['created_at', 'is_read']
    ordering = ['-created_at']

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

    @action(detail=False, methods=['get'])
    def unread(self, request):
        """Get unread notifications"""
        notifications = Notification.objects.filter(
            user=request.user,
            is_read=False
        )
        serializer = self.get_serializer(notifications, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def mark_as_read(self, request):
        """Mark notifications as read"""
        serializer = NotificationMarkReadSerializer(data=request.data)
        if serializer.is_valid():
            notification_ids = serializer.validated_data['notification_ids']
            Notification.objects.filter(
                id__in=notification_ids,
                user=request.user
            ).update(is_read=True)
            return Response({'message': 'Notifications marked as read'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def mark_all_as_read(self, request):
        """Mark all notifications as read"""
        Notification.objects.filter(user=request.user).update(is_read=True)
        return Response({'message': 'All notifications marked as read'})

    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Get count of unread notifications"""
        count = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).count()
        return Response({'unread_count': count})
