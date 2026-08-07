from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import FileExtensionValidator

User = get_user_model()

class Category(models.Model):
    """Categories for organizing learning materials"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    icon = models.CharField(max_length=50, blank=True)  # For UI icons
    slug = models.SlugField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']

    def __str__(self):
        return self.name


class EducationLevel(models.Model):
    """Education levels: Primary, Secondary, University, Professional, etc."""
    LEVEL_CHOICES = [
        ('primary', 'Primary School'),
        ('secondary', 'Secondary School'),
        ('university', 'University'),
        ('vocational', 'Vocational'),
        ('professional', 'Professional Development'),
        ('other', 'Other'),
    ]
    
    level = models.CharField(max_length=50, choices=LEVEL_CHOICES, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.get_level_display()


class Subject(models.Model):
    """Subjects for learning materials"""
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='subjects')
    education_level = models.ForeignKey(EducationLevel, on_delete=models.CASCADE, related_name='subjects')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('name', 'category', 'education_level')
        ordering = ['name']

    def __str__(self):
        return f"{self.name} - {self.education_level}"


class LearningMaterial(models.Model):
    """Main model for uploaded learning materials"""
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    FILE_TYPE_CHOICES = [
        ('pdf', 'PDF'),
        ('doc', 'Word Document'),
        ('ppt', 'Presentation'),
        ('video', 'Video'),
        ('image', 'Image'),
        ('other', 'Other'),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField()
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='materials')
    education_level = models.ForeignKey(EducationLevel, on_delete=models.CASCADE, related_name='materials')
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='uploaded_materials')
    
    file = models.FileField(
        upload_to='learning_materials/%Y/%m/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx', 'ppt', 'pptx', 'mp4', 'jpg', 'jpeg', 'png'])]
    )
    file_type = models.CharField(max_length=20, choices=FILE_TYPE_CHOICES)
    file_size = models.BigIntegerField()  # in bytes
    
    cover_image = models.ImageField(upload_to='covers/%Y/%m/', blank=True, null=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    review_notes = models.TextField(blank=True, null=True)  # Admin review comments
    
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # 0 = Free
    is_featured = models.BooleanField(default=False)
    
    download_count = models.IntegerField(default=0)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)  # Average rating
    total_reviews = models.IntegerField(default=0)
    
    tags = models.CharField(max_length=500, blank=True, help_text="Comma-separated tags")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    approved_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['uploaded_by', 'status']),
            models.Index(fields=['education_level', 'subject']),
        ]

    def __str__(self):
        return self.title

    @property
    def is_free(self):
        return self.price == 0
