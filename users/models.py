# users/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom User model for DMS.
    Stores system users: Administrator, Boarding Officer, Parent/Guardian.
    Extends AbstractUser to inherit built-in auth fields:
    username, email, first_name, last_name, is_active, date_joined, etc.
    """

    ROLE_CHOICES = (
        ('admin', 'Administrator'),
        ('officer', 'Boarding Officer'),
        ('parent', 'Parent/Guardian'),
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='parent',
        db_index=True,  # Index role for fast permission checks
    )
    phone = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        help_text="Contact phone number"
    )

    # Fix reverse accessor clashes — related_names must be unique per field
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='dms_user_groups',
        blank=True,
        verbose_name='groups',
        help_text='The groups this user belongs to.',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='dms_user_permissions',
        blank=True,
        verbose_name='user permissions',
        help_text='Specific permissions for this user.',
    )

    class Meta:
        db_table = 'dms_user'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['username']

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    # ── Convenience properties ──────────────────────────────
    @property
    def is_admin(self):
        return self.role == 'admin'

    @property
    def is_officer(self):
        return self.role == 'officer'

    @property
    def is_parent(self):
        return self.role == 'parent'

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.username