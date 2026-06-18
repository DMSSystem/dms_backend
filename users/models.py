# users/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
import random
import string
from typing import cast




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
        db_index=True,
    )
    phone = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        unique=True,
        help_text="Contact phone number e.g. +254712345678"
    )

    # ── Verification fields ─────────────────────────────────
    is_verified = models.BooleanField(
        default=False,
        help_text="True after the user has verified their email or phone OTP."
    )
    verification_method = models.CharField(
    max_length=10,
    default='email',
    editable=False,
)
    otp_code = models.CharField(
        max_length=6,
        blank=True,
        null=True,
    )
    otp_created_at = models.DateTimeField(
        blank=True,
        null=True,
    )
    otp_attempts = models.PositiveSmallIntegerField(
        default=0,
        help_text="Number of failed OTP verification attempts. Locked at 5."
    )

    # Fix reverse accessor clashes
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

    # ── Role properties ─────────────────────────────────────
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

    # ── OTP methods ─────────────────────────────────────────
    def generate_otp(self):
        """Generate a fresh 6-digit OTP, persist it, and return the code."""
        self.otp_code = ''.join(random.choices(string.digits, k=6))
        self.otp_created_at = timezone.now()
        self.otp_attempts = 0
        self.save(update_fields=['otp_code', 'otp_created_at', 'otp_attempts'])
        return self.otp_code

    def is_otp_valid(self, code):
        """
        Check if the submitted code is correct and not expired.
        - Expires after 10 minutes.
        - Locks after 5 failed attempts.
        - Increments otp_attempts on every call.
        """
        if not self.otp_code or not self.otp_created_at:
            return False
        if self.otp_attempts >= 5:
            return False
        expiry = self.otp_created_at + timezone.timedelta(minutes=10)
        if timezone.now() > expiry:
            return False
        self.otp_attempts += 1
        self.save(update_fields=['otp_attempts'])
        return self.otp_code == code

    def mark_verified(self):
        """Activate the account and clear all OTP fields."""
        self.is_verified = True
        self.is_active = True
        self.otp_code = None
        self.otp_created_at = None
        self.otp_attempts = 0
        self.save(update_fields=[
            'is_verified', 'is_active',
            'otp_code', 'otp_created_at', 'otp_attempts'
        ])