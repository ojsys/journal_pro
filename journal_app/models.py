from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Article(models.Model):
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('SUBMITTED', 'Submitted'),
        ('UNDER_REVIEW', 'Under Review'),
        ('REVISION_REQUIRED', 'Revision Required'),
        ('ACCEPTED', 'Accepted'),
        ('REJECTED', 'Rejected'),
        ('PUBLISHED', 'Published'),
    ]

    title = models.CharField(max_length=200)
    abstract = models.TextField()
    keywords = models.CharField(max_length=200)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='articles')
    content = models.TextField()
    file = models.FileField(upload_to='articles/')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    submission_date = models.DateTimeField(default=timezone.now)
    publication_date = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return self.title

class Review(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='reviews')
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    comments = models.TextField()
    recommendation = models.CharField(max_length=20, choices=[
        ('ACCEPT', 'Accept'),
        ('REVISE', 'Revise'),
        ('REJECT', 'Reject'),
    ])
    date_created = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['article', 'reviewer']

class Profile(models.Model):
    ROLES = [
        ('AUTHOR', 'Author'),
        ('REVIEWER', 'Reviewer'),
        ('EDITOR', 'Editor'),
        ('ADMIN', 'Administrator'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLES, default='AUTHOR')
    institution = models.CharField(max_length=200)
    bio = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.role}"