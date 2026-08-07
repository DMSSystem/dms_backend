from rest_framework import serializers
from models.download import Download
from .user_serializers import UserSerializer

class DownloadSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    material_title = serializers.CharField(source='material.title', read_only=True)
    
    class Meta:
        model = Download
        fields = [
            'id', 'user', 'material', 'material_title', 'download_date',
            'ip_address', 'device_info'
        ]
        read_only_fields = [
            'id', 'user', 'download_date', 'ip_address', 'device_info'
        ]


class DownloadCreateSerializer(serializers.ModelSerializer):
    """Serializer for recording downloads"""
    class Meta:
        model = Download
        fields = ['material']
