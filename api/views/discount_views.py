from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone

from models.discount import DiscountCode, DiscountRequest
from models.material import LearningMaterial
from serializers.discount_serializers import (
    DiscountCodeSerializer, DiscountCodeApplySerializer,
    DiscountRequestSerializer, DiscountRequestCreateSerializer,
    DiscountRequestApproveSerializer, DiscountRequestRejectSerializer
)


class DiscountCodeViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for discount codes"""
    serializer_class = DiscountCodeSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['is_active']
    search_fields = ['code']

    def get_queryset(self):
        return DiscountCode.objects.filter(user=self.request.user, is_active=True)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def apply(self, request):
        """Apply discount code to a purchase"""
        serializer = DiscountCodeApplySerializer(data=request.data)
        if serializer.is_valid():
            discount = serializer.validated_data['code']
            amount = serializer.validated_data['amount']
            
            discount_amount = discount.apply_discount(amount)
            final_amount = amount - discount_amount
            
            return Response({
                'code': discount.code,
                'original_amount': float(amount),
                'discount_amount': float(discount_amount),
                'final_amount': float(final_amount),
                'discount_type': discount.discount_type,
                'discount_value': float(discount.discount_value)
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def my_codes(self, request):
        """Get all discount codes for current user"""
        codes = DiscountCode.objects.filter(user=request.user)
        serializer = self.get_serializer(codes, many=True)
        return Response(serializer.data)


class DiscountRequestViewSet(viewsets.ModelViewSet):
    """ViewSet for discount requests"""
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status']
    ordering = ['-created_at']

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return DiscountRequest.objects.all()
        return DiscountRequest.objects.filter(requested_by=user)

    def get_serializer_class(self):
        if self.action == 'create':
            return DiscountRequestCreateSerializer
        elif self.action == 'approve':
            return DiscountRequestApproveSerializer
        elif self.action == 'reject':
            return DiscountRequestRejectSerializer
        return DiscountRequestSerializer

    def perform_create(self, serializer):
        """Create discount request with current user"""
        serializer.save(requested_by=self.request.user)

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def approve(self, request, pk=None):
        """Admin action to approve discount request"""
        discount_request = self.get_object()
        
        approved_percentage = request.data.get(
            'approved_discount_percentage',
            discount_request.requested_discount_percentage
        )
        
        discount_request.requested_discount_percentage = approved_percentage
        discount_request.approve(reviewed_by=request.user)

        # Create notification
        from models.extras import Notification
        Notification.objects.create(
            user=discount_request.requested_by,
            notification_type='discount_earned',
            title='Discount Approved',
            message=f'Your discount request has been approved! You earned a {approved_percentage}% discount.',
            material=discount_request.material,
            action_url=f'/discounts/'
        )

        serializer = self.get_serializer(discount_request)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def reject(self, request, pk=None):
        """Admin action to reject discount request"""
        discount_request = self.get_object()
        reason = request.data.get('rejection_reason', 'No reason provided')
        
        discount_request.reject(reviewed_by=request.user, notes=reason)

        # Create notification
        from models.extras import Notification
        Notification.objects.create(
            user=discount_request.requested_by,
            notification_type='discount_rejected',
            title='Discount Request Rejected',
            message=f'Your discount request was rejected. Reason: {reason}',
            material=discount_request.material
        )

        serializer = self.get_serializer(discount_request)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[IsAdminUser])
    def pending(self, request):
        """Get pending discount requests for admin review"""
        requests = DiscountRequest.objects.filter(status='pending')
        serializer = self.get_serializer(requests, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def my_requests(self, request):
        """Get current user's discount requests"""
        requests = DiscountRequest.objects.filter(requested_by=request.user)
        serializer = self.get_serializer(requests, many=True)
        return Response(serializer.data)
