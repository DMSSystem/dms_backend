from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

class Favorite(models.Model):
    """Users can favorite learning materials"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    material = models.ForeignKey('material.LearningMaterial', on_delete=models.CASCADE, related_name='favorited_by')
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'material')
        ordering = ['-added_at']
        indexes = [
            models.Index(fields=['user', 'added_at']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.material.title}"


class Collection(models.Model):
    """Collections/playlists of materials created by users"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='collections')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    materials = models.ManyToManyField('material.LearningMaterial', related_name='in_collections', through='CollectionItem')
    
    is_public = models.BooleanField(default=False)
    cover_image = models.ImageField(upload_to='collections/%Y/%m/', blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ('user', 'name')
        indexes = [
            models.Index(fields=['user', 'is_public']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.name}"


class CollectionItem(models.Model):
    """Items in a collection with ordering"""
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE, related_name='items')
    material = models.ForeignKey('material.LearningMaterial', on_delete=models.CASCADE)
    order = models.PositiveIntegerField()  # Order in collection
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('collection', 'material')
        ordering = ['order']

    def __str__(self):
        return f"{self.collection.name} - {self.material.title}"


class Notification(models.Model):
    """Notifications for users"""
    NOTIFICATION_TYPE_CHOICES = [
        ('material_approved', 'Material Approved'),
        ('material_rejected', 'Material Rejected'),
        ('discount_earned', 'Discount Earned'),
        ('new_download', 'Your Material Downloaded'),
        ('review_posted', 'New Review'),
        ('sale_notification', 'Sale Notification'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPE_CHOICES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    
    material = models.ForeignKey('material.LearningMaterial', on_delete=models.SET_NULL, null=True, blank=True)
    related_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='notifications_about_me')
    
    is_read = models.BooleanField(default=False)
    action_url = models.CharField(max_length=500, blank=True)  # Link to relevant page
    
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read', 'created_at']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.notification_type}"

    def mark_as_read(self):
        self.is_read = True
        self.read_at = timezone.now()
        self.save()


class AuditLog(models.Model):
    """Audit trail for admin actions"""
    ACTION_CHOICES = [
        ('material_approved', 'Material Approved'),
        ('material_rejected', 'Material Rejected'),
        ('discount_approved', 'Discount Approved'),
        ('discount_rejected', 'Discount Rejected'),
        ('user_suspended', 'User Suspended'),
        ('user_deleted', 'User Deleted'),
        ('material_deleted', 'Material Deleted'),
    ]

    admin = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='audit_logs')
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    
    target_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_actions_on_me')
    material = models.ForeignKey('material.LearningMaterial', on_delete=models.SET_NULL, null=True, blank=True)
    
    details = models.TextField()  # JSON details of the action
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['admin', 'created_at']),
            models.Index(fields=['action', 'created_at']),
        ]

    def __str__(self):
        return f"{self.admin.username} - {self.action}"
