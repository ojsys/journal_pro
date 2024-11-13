# models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse

class Department(models.Model):
    DEPARTMENT_CHOICES = [
        ('ENGLISH', 'Department of English'),
        ('LITERARY', 'Literary Studies'),
        ('GST', 'General Studies')
    ]
    
    name = models.CharField(max_length=100, choices=DEPARTMENT_CHOICES)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    head_of_dept = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='headed_department')
    email = models.EmailField()
    website_title = models.CharField(max_length=200)
    logo = models.ImageField(upload_to='department_logos/', null=True, blank=True)
    
    def __str__(self):
        return self.get_name_display()
    
    def get_absolute_url(self):
        return reverse('department_home', kwargs={'dept_slug': self.slug})

class Profile(models.Model):
    ROLES = [
        ('AUTHOR', 'Author'),
        ('REVIEWER', 'Reviewer'),
        ('EDITOR', 'Editor'),
        ('ADMIN', 'Administrator'),
        ('DEPT_ADMIN', 'Department Administrator')
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    departments = models.ManyToManyField(Department, related_name='members')
    role = models.CharField(max_length=20, choices=ROLES, default='AUTHOR')
    institution = models.CharField(max_length=200)
    bio = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.role}"

class Journal(models.Model):
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='journals')
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    issn = models.CharField(max_length=9, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.title} - {self.department.name}"

class Volume(models.Model):
    journal = models.ForeignKey(Journal, on_delete=models.CASCADE, related_name='volumes')
    number = models.PositiveIntegerField()
    year = models.PositiveIntegerField()
    is_current = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['journal', 'number']
        ordering = ['-year', '-number']

class Issue(models.Model):
    volume = models.ForeignKey(Volume, on_delete=models.CASCADE, related_name='issues')
    number = models.PositiveIntegerField()
    publication_date = models.DateField()
    is_special_issue = models.BooleanField(default=False)
    special_issue_title = models.CharField(max_length=200, blank=True, null=True)
    
    class Meta:
        unique_together = ['volume', 'number']
        ordering = ['-publication_date']

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

    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='articles')
    issue = models.ForeignKey(Issue, on_delete=models.CASCADE, related_name='articles', null=True, blank=True)
    title = models.CharField(max_length=200)
    abstract = models.TextField()
    keywords = models.CharField(max_length=200)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='articles')
    co_authors = models.ManyToManyField(User, related_name='co_authored_articles', blank=True)
    content = models.TextField()
    file = models.FileField(upload_to='articles/%Y/%m/')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    submission_date = models.DateTimeField(default=timezone.now)
    publication_date = models.DateTimeField(null=True, blank=True)
    doi = models.CharField(max_length=100, blank=True, null=True)
    
    class Meta:
        ordering = ['-submission_date']
    
    def __str__(self):
        return self.title

class Review(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='reviews')
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    comments = models.TextField()
    recommendation = models.CharField(max_length=20, choices=[
        ('ACCEPT', 'Accept'),
        ('MINOR_REVISION', 'Minor Revision'),
        ('MAJOR_REVISION', 'Major Revision'),
        ('REJECT', 'Reject'),
    ])
    date_created = models.DateTimeField(auto_now_add=True)
    is_complete = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['article', 'reviewer']

class DepartmentSettings(models.Model):
    department = models.OneToOneField(Department, on_delete=models.CASCADE, related_name='settings')
    submission_guidelines = models.TextField()
    review_guidelines = models.TextField()
    publication_frequency = models.CharField(max_length=100)
    peer_review_type = models.CharField(max_length=50, choices=[
        ('DOUBLE_BLIND', 'Double Blind'),
        ('SINGLE_BLIND', 'Single Blind'),
        ('OPEN', 'Open Review')
    ])
    contact_email = models.EmailField()
    theme_color = models.CharField(max_length=7, default='#000000')  # Hex color code