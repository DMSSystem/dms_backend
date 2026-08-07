"""
Database Models for Learning Materials Marketplace

This package contains all Django models for the learning materials marketplace platform.

Models included:
1. User - Extended user model with teacher/student/admin roles
2. Material Models:
   - Category, EducationLevel, Subject, LearningMaterial
3. Download - Track file downloads
4. Discount Models:
   - DiscountCode, DiscountRequest
5. Review Models:
   - Review, HelpfulReview
6. Transaction Models:
   - Transaction, UserBalance
7. Extra Models:
   - Favorite, Collection, CollectionItem
   - Notification, AuditLog
"""

from .user import User
from .material import Category, EducationLevel, Subject, LearningMaterial
from .download import Download
from .discount import DiscountCode, DiscountRequest
from .review import Review, HelpfulReview
from .transaction import Transaction, UserBalance
from .extras import Favorite, Collection, CollectionItem, Notification, AuditLog

__all__ = [
    'User',
    'Category',
    'EducationLevel',
    'Subject',
    'LearningMaterial',
    'Download',
    'DiscountCode',
    'DiscountRequest',
    'Review',
    'HelpfulReview',
    'Transaction',
    'UserBalance',
    'Favorite',
    'Collection',
    'CollectionItem',
    'Notification',
    'AuditLog',
]
