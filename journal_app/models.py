# models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse
import uuid

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
    head_of_dept = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='headed_department')
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
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
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
    editor_in_chief = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='edited_journals')
    editorial_board = models.ManyToManyField(User, related_name='board_member_of')
    cover_image = models.ImageField(upload_to='journal_covers/', null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.department.name})"

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
    journal = models.ForeignKey(Journal, on_delete=models.CASCADE, related_name='articles')
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    abstract = models.TextField()
    keywords = models.CharField(max_length=200)
    
    # Authors Information
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='articles')
    co_authors = models.ManyToManyField(User, related_name='co_authored_articles', blank=True)
    corresponding_author = models.ForeignKey(
        User, 
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
    volume = models.ForeignKey('Volume', on_delete=models.SET_NULL, null=True, related_name='articles')
    issue = models.ForeignKey('Issue', on_delete=models.SET_NULL, null=True, related_name='articles')
    citation_count = models.PositiveIntegerField(default=0)
    
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

    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='files')
    file = models.FileField(upload_to='article_files/%Y/%m/')
    file_type = models.CharField(max_length=20, choices=FILE_TYPES)
    version = models.PositiveIntegerField(default=1)
    description = models.TextField(blank=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    upload_date = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-upload_date', '-version']

class Review(models.Model):
    RECOMMENDATION_CHOICES = [
        ('ACCEPT', 'Accept'),
        ('MINOR_REVISION', 'Minor Revision'),
        ('MAJOR_REVISION', 'Major Revision'),
        ('REJECT', 'Reject')
    ]

    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='reviews')
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
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
    
    # Attachments
    attachments = models.ManyToManyField('ReviewAttachment', related_name='review', blank=True)
    
    class Meta:
        unique_together = ['article', 'reviewer']
        ordering = ['-assigned_date']

    def save(self, *args, **kwargs):
        if not self.due_date:
            # Set due date based on department settings
            days = self.article.department.settings.review_deadline_days
            self.due_date = timezone.now() + timezone.timedelta(days=days)
        super().save(*args, **kwargs)

class ReviewAttachment(models.Model):
    file = models.FileField(upload_to='review_attachments/%Y/%m/')
    description = models.CharField(max_length=200)
    uploaded_at = models.DateTimeField(auto_now_add=True)

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
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=100)
    details = models.TextField()
    ip_address = models.GenericIPAddressField(null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']