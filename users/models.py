# users/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    """
    Custom User model for DMS
    Stores system users: Administrator, Boarding Officer, Parent/Guardian
    """
    ROLE_CHOICES = (
        ('admin', 'Administrator'),
        ('officer', 'Boarding Officer'),
        ('parent', 'Parent/Guardian'),
    )
    
    # Add custom fields
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='parent')
    
    # Fix reverse accessor clashes by setting unique related_name
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='dms_users',  # Changed to avoid clash
        blank=True,
        verbose_name='groups',
        help_text='The groups this user belongs to.',
    )
    
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='dms_users',  # Changed to avoid clash
        blank=True,
        verbose_name='user permissions',
        help_text='Specific permissions for this user.',
    )
    
    class Meta:
        db_table = 'user'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"