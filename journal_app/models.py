# models.py

from django.db import models
from django.contrib.auth.models import User, AbstractUser, BaseUserManager
from django.utils import timezone
from django.urls import reverse
import uuid
from django.conf import settings


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)

class CustomUser(AbstractUser):
    username = None
    email = models.EmailField('email address', unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

class Department(models.Model):
    DEPARTMENT_CHOICES = [
        ('ENGLISH', 'Department of English'),
        ('LITERARY', 'Literary Studies'),
        ('GST', 'General Studies')
    ]
    
    name = models.CharField(max_length=100, choices=DEPARTMENT_CHOICES, unique=True)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    established_date = models.DateField()
    head_of_dept = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='headed_department')
    faculty_members = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='faculty_departments', blank=True)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField()
    website_title = models.CharField(max_length=200)
    logo = models.ImageField(upload_to='department_logos/', null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.get_name_display()

    def get_absolute_url(self):
        return reverse('department_home', kwargs={'dept_slug': self.slug})

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
    max_reviewers_per_article = models.PositiveIntegerField(default=3)
    review_deadline_days = models.PositiveIntegerField(default=30)
    allow_public_submissions = models.BooleanField(default=True)
    require_author_registration = models.BooleanField(default=True)
    contact_email = models.EmailField()
    theme_color = models.CharField(max_length=7, default='#000000')
    enable_doi = models.BooleanField(default=False)
    enable_plagiarism_check = models.BooleanField(default=False)
    enable_author_tracking = models.BooleanField(default=True)
    notification_settings = models.JSONField(default=dict)

    def __str__(self):
        return f"Settings for {self.department.name}"

class Profile(models.Model):
    ROLES = [
        ('AUTHOR', 'Author'),
        ('REVIEWER', 'Reviewer'),
        ('EDITOR', 'Editor'),
        ('DEPT_ADMIN', 'Department Administrator'),
        ('ADMIN', 'Administrator')
    ]
    
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    departments = models.ManyToManyField(Department, related_name='members')
    role = models.CharField(max_length=20, choices=ROLES, default='AUTHOR')
    institution = models.CharField(max_length=200)
    academic_title = models.CharField(max_length=100, blank=True)
    bio = models.TextField(blank=True)
    expertise = models.CharField(max_length=200, blank=True)
    orcid_id = models.CharField(max_length=20, blank=True)
    public_email = models.EmailField(blank=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    reviews_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.role}"

    def increment_reviews_count(self):
        self.reviews_count += 1
        self.save()

class Journal(models.Model):
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='journals')
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    issn = models.CharField(max_length=9, blank=True, null=True)
    editor_in_chief = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='edited_journals')
    editorial_board = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='board_member_of')
    cover_image = models.ImageField(upload_to='journal_covers/', null=True, blank=True)
    latest_issue_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.department.name})"

class Volume(models.Model):
    journal = models.ForeignKey(Journal, on_delete=models.CASCADE, related_name='volumes')
    number = models.PositiveIntegerField()
    year = models.PositiveIntegerField()
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    is_current = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['journal', 'number']
        ordering = ['-year', '-number']

    def __str__(self):
        return f"Volume {self.number} ({self.year}) - {self.journal.title}"

class Issue(models.Model):
    volume = models.ForeignKey(Volume, on_delete=models.CASCADE, related_name='issues')
    number = models.PositiveIntegerField()
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    publication_date = models.DateField()
    is_special_issue = models.BooleanField(default=False)
    special_issue_title = models.CharField(max_length=200, blank=True, null=True)
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['volume', 'number']
        ordering = ['-publication_date']

    def __str__(self):
        return f"Issue {self.number} - {self.volume}"

class Article(models.Model):
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('SUBMITTED', 'Submitted'),
        ('UNDER_REVIEW', 'Under Review'),
        ('REVISION_REQUIRED', 'Revision Required'),
        ('ACCEPTED', 'Accepted'),
        ('REJECTED', 'Rejected'),
        ('PUBLISHED', 'Published'),
        ('RETRACTED', 'Retracted')
    ]

    # Basic Information
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='articles')
    journal = models.ForeignKey(Journal, on_delete=models.CASCADE, related_name='journal_articles')
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    abstract = models.TextField()
    keywords = models.CharField(max_length=200)
    
    # Authors Information
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='authored_articles')
    co_authors = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='coauthored_articles', blank=True)
    corresponding_author = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='corresponding_articles'
    )
    
    # Content and Files
    content = models.TextField()
    manuscript_file = models.FileField(upload_to='manuscripts/%Y/%m/')
    supplementary_files = models.ManyToManyField('ArticleFile', related_name='supplementary_to', blank=True)
    
    # Status and Tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    submission_date = models.DateTimeField(default=timezone.now)
    acceptance_date = models.DateTimeField(null=True, blank=True)
    publication_date = models.DateTimeField(null=True, blank=True)
    version = models.PositiveIntegerField(default=1)
    
    # Metadata
    doi = models.CharField(max_length=100, blank=True, null=True)
    page_numbers = models.CharField(max_length=50, blank=True)
    volume = models.ForeignKey(Volume, on_delete=models.SET_NULL, null=True, related_name='volume_articles')
    issue = models.ForeignKey(Issue, on_delete=models.SET_NULL, null=True, related_name='issue_articles')
    citation_count = models.PositiveIntegerField(default=0)
    download_count = models.PositiveIntegerField(default=0)
    
    # Flags and Settings
    is_featured = models.BooleanField(default=False)
    requires_ethics_statement = models.BooleanField(default=False)
    ethics_statement = models.TextField(blank=True)
    competing_interests = models.TextField(blank=True)
    funding_information = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-submission_date']
        unique_together = ['journal', 'slug']

    def __str__(self):
        return self.title

    def generate_doi(self):
        if not self.doi and self.department.settings.enable_doi:
            # Implement DOI generation logic
            pass

class ArticleFile(models.Model):
    FILE_TYPES = [
        ('MANUSCRIPT', 'Manuscript'),
        ('FIGURE', 'Figure'),
        ('TABLE', 'Table'),
        ('SUPPLEMENT', 'Supplementary Material'),
        ('REVISION', 'Revision'),
        ('RESPONSE', 'Response to Reviewers')
    ]

    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='article_files')
    file = models.FileField(upload_to='article_files/%Y/%m/')
    file_type = models.CharField(max_length=20, choices=FILE_TYPES)
    version = models.PositiveIntegerField(default=1)
    description = models.TextField(blank=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    upload_date = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-upload_date', '-version']


# ----------- Research Areas ----------------

class ResearchArea(models.Model):
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    description = models.TextField()
    
    def __str__(self):
        return self.name

class Event(models.Model):
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()
    date = models.DateField()
    time = models.TimeField()
    location = models.CharField(max_length=200)
    registration_required = models.BooleanField(default=False)
    registration_link = models.URLField(blank=True, null=True)
    
    def __str__(self):
        return self.title

# ---------------- Reviews ---------------------
class Review(models.Model):
    RECOMMENDATION_CHOICES = [
        ('ACCEPT', 'Accept'),
        ('MINOR_REVISION', 'Minor Revision'),
        ('MAJOR_REVISION', 'Major Revision'),
        ('REJECT', 'Reject')
    ]

    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='article_reviews')
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviewer_reviews')
    assigned_date = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField()
    completion_date = models.DateTimeField(null=True, blank=True)
    
    # Review Details
    comments_to_editor = models.TextField()
    comments_to_author = models.TextField()
    recommendation = models.CharField(max_length=20, choices=RECOMMENDATION_CHOICES)
    is_complete = models.BooleanField(default=False)
    
    # Review Form Responses
    review_form_responses = models.JSONField(null=True, blank=True)
    confidential_comments = models.TextField(blank=True)
    
    class Meta:
        unique_together = ['article', 'reviewer']
        ordering = ['-assigned_date']

    def save(self, *args, **kwargs):
        if not self.due_date:
            # Set due date based on department settings
            days = self.article.department.settings.review_deadline_days
            self.due_date = timezone.now() + timezone.timedelta(days=days)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Review for {self.article.title} by {self.reviewer.username}"

class ReviewAttachment(models.Model):
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='review_files')
    file = models.FileField(upload_to='review_attachments/%Y/%m/')
    description = models.CharField(max_length=255)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Attachment for {self.review}"

class EmailLog(models.Model):
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='email_logs')
    subject = models.CharField(max_length=200)
    recipient = models.EmailField()
    content = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20)
    related_article = models.ForeignKey(Article, on_delete=models.SET_NULL, null=True, blank=True)
    related_review = models.ForeignKey(Review, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['-sent_at']

class AuditLog(models.Model):
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='audit_logs')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=100)
    details = models.TextField()
    ip_address = models.GenericIPAddressField(null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']