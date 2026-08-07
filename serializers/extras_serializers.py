from rest_framework import serializers
from models.extras import Favorite, Collection, CollectionItem, Notification, AuditLog
from .user_serializers import UserSerializer
from .material_serializers import LearningMaterialListSerializer

class FavoriteSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    material = LearningMaterialListSerializer(read_only=True)
    
    class Meta:
        model = Favorite
        fields = ['id', 'user', 'material', 'added_at']
        read_only_fields = ['id', 'user', 'added_at']


class CollectionItemSerializer(serializers.ModelSerializer):
    material = LearningMaterialListSerializer(read_only=True)
    
    class Meta:
        model = CollectionItem
        fields = ['id', 'collection', 'material', 'order', 'added_at']
        read_only_fields = ['id', 'added_at']


class CollectionSerializer(serializers.ModelSerializer):
    items = CollectionItemSerializer(many=True, read_only=True)
    user = UserSerializer(read_only=True)
    material_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Collection
        fields = [
            'id', 'user', 'name', 'description', 'is_public',
            'cover_image', 'material_count', 'items',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

    def get_material_count(self, obj):
        return obj.materials.count()


class CollectionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating collections"""
    class Meta:
        model = Collection
        fields = ['name', 'description', 'is_public', 'cover_image']


class NotificationSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Notification
        fields = [
            'id', 'user', 'notification_type', 'title', 'message',
            'material', 'related_user', 'is_read', 'action_url',
            'created_at', 'read_at'
        ]
        read_only_fields = fields


class NotificationMarkReadSerializer(serializers.Serializer):
    """Serializer for marking notifications as read"""
    notification_ids = serializers.ListField(child=serializers.IntegerField())


class AuditLogSerializer(serializers.ModelSerializer):
    admin = UserSerializer(read_only=True)
    target_user = UserSerializer(read_only=True)
    
    class Meta:
        model = AuditLog
        fields = [
            'id', 'admin', 'action', 'target_user', 'material',
            'details', 'ip_address', 'created_at'
        ]
        read_only_fields = fields
