"""
Serializers package for Learning Materials Marketplace API

This package contains all DRF serializers for API endpoints.

Serializers included:
1. UserSerializers - User and profile serializers
2. MaterialSerializers - Category, Subject, Material serializers
3. DiscountSerializers - Discount code and request serializers
4. ReviewSerializers - Review and helpful review serializers
5. DownloadSerializers - Download tracking serializers
6. TransactionSerializers - Payment and balance serializers
7. ExtrasSerializers - Favorites, Collections, Notifications, Audits
"""

from .user_serializers import (
    UserSerializer, UserProfileSerializer, UserDetailSerializer
)
from .material_serializers import (
    CategorySerializer, EducationLevelSerializer, SubjectSerializer,
    LearningMaterialListSerializer, LearningMaterialDetailSerializer,
    LearningMaterialCreateSerializer
)
from .discount_serializers import (
    DiscountCodeSerializer, DiscountCodeApplySerializer,
    DiscountRequestSerializer, DiscountRequestCreateSerializer,
    DiscountRequestApproveSerializer, DiscountRequestRejectSerializer
)
from .review_serializers import (
    ReviewSerializer, ReviewCreateSerializer, ReviewUpdateSerializer,
    HelpfulReviewSerializer, HelpfulReviewToggleSerializer
)
from .download_serializers import (
    DownloadSerializer, DownloadCreateSerializer
)
from .transaction_serializers import (
    TransactionSerializer, UserBalanceSerializer,
    PurchaseSerializer, RefundSerializer
)
from .extras_serializers import (
    FavoriteSerializer, CollectionSerializer, CollectionCreateSerializer,
    CollectionItemSerializer, NotificationSerializer,
    NotificationMarkReadSerializer, AuditLogSerializer
)

__all__ = [
    'UserSerializer',
    'UserProfileSerializer',
    'UserDetailSerializer',
    'CategorySerializer',
    'EducationLevelSerializer',
    'SubjectSerializer',
    'LearningMaterialListSerializer',
    'LearningMaterialDetailSerializer',
    'LearningMaterialCreateSerializer',
    'DiscountCodeSerializer',
    'DiscountCodeApplySerializer',
    'DiscountRequestSerializer',
    'DiscountRequestCreateSerializer',
    'DiscountRequestApproveSerializer',
    'DiscountRequestRejectSerializer',
    'ReviewSerializer',
    'ReviewCreateSerializer',
    'ReviewUpdateSerializer',
    'HelpfulReviewSerializer',
    'HelpfulReviewToggleSerializer',
    'DownloadSerializer',
    'DownloadCreateSerializer',
    'TransactionSerializer',
    'UserBalanceSerializer',
    'PurchaseSerializer',
    'RefundSerializer',
    'FavoriteSerializer',
    'CollectionSerializer',
    'CollectionCreateSerializer',
    'CollectionItemSerializer',
    'NotificationSerializer',
    'NotificationMarkReadSerializer',
    'AuditLogSerializer',
]
