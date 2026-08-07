from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404

from models.material import Category, EducationLevel, Subject, LearningMaterial
from serializers.material_serializers import (
    CategorySerializer, EducationLevelSerializer, SubjectSerializer,
    LearningMaterialListSerializer, LearningMaterialDetailSerializer,
    LearningMaterialCreateSerializer
)

class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for material categories"""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'description']
    lookup_field = 'slug'


class EducationLevelViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for education levels"""
    queryset = EducationLevel.objects.all()
    serializer_class = EducationLevelSerializer
    permission_classes = [AllowAny]


class SubjectViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for subjects"""
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['category', 'education_level']
    search_fields = ['name', 'description']


class LearningMaterialViewSet(viewsets.ModelViewSet):
    """ViewSet for learning materials"""
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'subject', 'education_level', 'is_featured']
    search_fields = ['title', 'description', 'tags']
    ordering_fields = ['created_at', 'download_count', 'rating']
    ordering = ['-created_at']

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return LearningMaterial.objects.all()
        return LearningMaterial.objects.filter(status='approved')

    def get_serializer_class(self):
        if self.action == 'create' or self.action == 'update':
            return LearningMaterialCreateSerializer
        elif self.action == 'retrieve':
            return LearningMaterialDetailSerializer
        return LearningMaterialListSerializer

    def perform_create(self, serializer):
        """Create material with current user as uploader"""
        serializer.save(uploaded_by=self.request.user, status='pending')

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def download(self, request, pk=None):
        """Record a download and provide file URL"""
        material = self.get_object()
        
        # Record download
        from models.download import Download
        Download.objects.create(
            user=request.user,
            material=material,
            ip_address=self.get_client_ip(request),
            device_info=request.META.get('HTTP_USER_AGENT', '')
        )
        
        # Update download count
        material.download_count += 1
        material.save(update_fields=['download_count'])
        
        # Update user download count
        request.user.total_downloads += 1
        request.user.save(update_fields=['total_downloads'])

        return Response({
            'message': 'Download recorded successfully',
            'file_url': material.file.url,
            'file_name': material.file.name
        })

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def approve(self, request, pk=None):
        """Admin action to approve material"""
        material = self.get_object()
        material.status = 'approved'
        material.approved_at = timezone.now()
        material.save()

        # Create notification
        from models.extras import Notification
        Notification.objects.create(
            user=material.uploaded_by,
            notification_type='material_approved',
            title='Material Approved',
            message=f'Your material "{material.title}" has been approved!',
            material=material,
            action_url=f'/materials/{material.id}/'
        )

        return Response({'status': 'Material approved'})

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def reject(self, request, pk=None):
        """Admin action to reject material"""
        material = self.get_object()
        material.status = 'rejected'
        material.review_notes = request.data.get('reason', '')
        material.save()

        # Create notification
        from models.extras import Notification
        Notification.objects.create(
            user=material.uploaded_by,
            notification_type='material_rejected',
            title='Material Rejected',
            message=f'Your material "{material.title}" was rejected. Reason: {material.review_notes}',
            material=material
        )

        return Response({'status': 'Material rejected'})

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def my_uploads(self, request):
        """Get current user's uploaded materials"""
        materials = LearningMaterial.objects.filter(uploaded_by=request.user)
        serializer = self.get_serializer(materials, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def pending_review(self, request):
        """Admin action to get materials pending review"""
        if not request.user.is_staff:
            return Response(
                {'error': 'Only admins can access this'},
                status=status.HTTP_403_FORBIDDEN
            )
        materials = LearningMaterial.objects.filter(status='pending')
        serializer = self.get_serializer(materials, many=True)
        return Response(serializer.data)

    @staticmethod
    def get_client_ip(request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
