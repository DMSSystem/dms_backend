from rest_framework import serializers
from models.transaction import Transaction, UserBalance
from .user_serializers import UserSerializer

class TransactionSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Transaction
        fields = [
            'id', 'user', 'material', 'transaction_type', 'status',
            'original_amount', 'discount_amount', 'final_amount',
            'discount_code', 'payment_method', 'payment_reference',
            'description', 'notes', 'created_at', 'completed_at'
        ]
        read_only_fields = fields


class UserBalanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserBalance
        fields = [
            'user', 'total_earned', 'total_spent', 'current_balance',
            'wallet_balance', 'last_updated'
        ]
        read_only_fields = fields


class PurchaseSerializer(serializers.Serializer):
    """Serializer for processing purchases"""
    material_id = serializers.IntegerField()
    discount_code = serializers.CharField(required=False, allow_blank=True)
    payment_method = serializers.ChoiceField(choices=['stripe', 'paypal', 'card'])


class RefundSerializer(serializers.Serializer):
    """Serializer for processing refunds"""
    transaction_id = serializers.CharField()
    reason = serializers.CharField(max_length=500)
