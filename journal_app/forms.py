# forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import (Department, DepartmentSettings, Profile, Journal, Article, 
                    ArticleFile, Review, ReviewAttachment)

class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ['name', 'description', 'established_date', 'head_of_dept', 
                 'email', 'phone', 'address', 'website_title', 'logo', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'established_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'website_title': forms.TextInput(attrs={'class': 'form-control'}),
            'logo': forms.FileInput(attrs={'class': 'form-control'}),
        }

class DepartmentSettingsForm(forms.ModelForm):
    class Meta:
        model = DepartmentSettings
        fields = ['submission_guidelines', 'review_guidelines', 'publication_frequency',
                 'peer_review_type', 'max_reviewers_per_article', 'review_deadline_days',
                 'allow_public_submissions', 'require_author_registration',
                 'contact_email', 'theme_color', 'enable_doi', 'enable_plagiarism_check',
                 'enable_author_tracking', 'notification_settings']
        widgets = {
            'submission_guidelines': forms.Textarea(attrs={'rows': 6, 'class': 'form-control'}),
            'review_guidelines': forms.Textarea(attrs={'rows': 6, 'class': 'form-control'}),
            'publication_frequency': forms.TextInput(attrs={'class': 'form-control'}),
            'peer_review_type': forms.Select(attrs={'class': 'form-select'}),
            'max_reviewers_per_article': forms.NumberInput(attrs={'class': 'form-control'}),
            'review_deadline_days': forms.NumberInput(attrs={'class': 'form-control'}),
            'contact_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'theme_color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control'}),
        }

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    departments = forms.ModelMultipleChoiceField(
        queryset=Department.objects.filter(is_active=True),
        widget=forms.CheckboxSelectMultiple,
        required=True
    )
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'first_name', 'last_name')

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['role', 'institution', 'academic_title', 'bio', 'expertise',
                 'orcid_id', 'public_email', 'profile_picture']
        widgets = {
            'role': forms.Select(attrs={'class': 'form-select'}),
            'institution': forms.TextInput(attrs={'class': 'form-control'}),
            'academic_title': forms.TextInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'expertise': forms.TextInput(attrs={'class': 'form-control'}),
            'orcid_id': forms.TextInput(attrs={'class': 'form-control'}),
            'public_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
        }

class JournalForm(forms.ModelForm):
    class Meta:
        model = Journal
        fields = ['department', 'title', 'description', 'issn', 'editor_in_chief',
                 'editorial_board', 'cover_image', 'is_active']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'issn': forms.TextInput(attrs={'class': 'form-control'}),
            'cover_image': forms.FileInput(attrs={'class': 'form-control'}),
        }

class ArticleSubmissionForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = ['journal', 'title', 'abstract', 'keywords', 'co_authors',
                 'corresponding_author', 'content', 'manuscript_file',
                 'requires_ethics_statement', 'ethics_statement',
                 'competing_interests', 'funding_information']
        widgets = {
            'journal': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'abstract': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'keywords': forms.TextInput(attrs={'class': 'form-control'}),
            'co_authors': forms.SelectMultiple(attrs={'class': 'form-select'}),
            'corresponding_author': forms.Select(attrs={'class': 'form-select'}),
            'content': forms.Textarea(attrs={'rows': 8, 'class': 'form-control'}),
            'manuscript_file': forms.FileInput(attrs={'class': 'form-control'}),
            'ethics_statement': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'competing_interests': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'funding_information': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
        }

    def __init__(self, *args, department=None, **kwargs):
        super().__init__(*args, **kwargs)
        if department:
            self.fields['journal'].queryset = Journal.objects.filter(department=department)
            self.fields['co_authors'].queryset = User.objects.filter(
                profile__departments=department
            ).exclude(id=kwargs.get('initial', {}).get('author'))

class ArticleFileForm(forms.ModelForm):
    class Meta:
        model = ArticleFile
        fields = ['file', 'file_type', 'description']
        widgets = {
            'file': forms.FileInput(attrs={'class': 'form-control'}),
            'file_type': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

class ReviewForm(forms.ModelForm):
    attachments = forms.FileField(
        widget=forms.ClearableFileInput(attrs={'multiple': True, 'class': 'form-control'}),
        required=False
    )

    class Meta:
        model = Review
        fields = ['comments_to_editor', 'comments_to_author', 'recommendation',
                 'review_form_responses', 'confidential_comments']
        widgets = {
            'comments_to_editor': forms.Textarea(attrs={'rows': 6, 'class': 'form-control'}),
            'comments_to_author': forms.Textarea(attrs={'rows': 6, 'class': 'form-control'}),
            'recommendation': forms.Select(attrs={'class': 'form-select'}),
            'confidential_comments': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
        }

    def save(self, commit=True):
        review = super().save(commit=False)
        if commit:
            review.is_complete = True
            review.completion_date = timezone.now()
            review.save()
            
            # Handle attachments
            attachments = self.cleaned_data.get('attachments')
            if attachments:
                for attachment in attachments:
                    ReviewAttachment.objects.create(
                        review=review,
                        file=attachment,
                        description=f"Review attachment for {review.article.title}"
                    )
        return review

class ReviewAssignmentForm(forms.Form):
    reviewers = forms.ModelMultipleChoiceField(
        queryset=None,
        widget=forms.CheckboxSelectMultiple,
        required=True
    )
    due_date = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'})
    )
    message_to_reviewers = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
        required=False
    )

    def __init__(self, *args, department=None, **kwargs):
        super().__init__(*args, **kwargs)
        if department:
            self.fields['reviewers'].queryset = User.objects.filter(
                profile__role='REVIEWER',
                profile__departments=department
            )

class ReviewResponseForm(forms.Form):
    decision = forms.ChoiceField(
        choices=[
            ('ACCEPT', 'Accept'),
            ('REVISION_REQUIRED', 'Revision Required'),
            ('REJECT', 'Reject')
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    feedback_to_author = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 6, 'class': 'form-control'})
    )
    internal_comments = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
        required=False
    )
    send_notification = forms.BooleanField(
        initial=True,
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

class BulkArticleActionForm(forms.Form):
    articles = forms.ModelMultipleChoiceField(
        queryset=None,
        widget=forms.CheckboxSelectMultiple
    )
    action = forms.ChoiceField(
        choices=[
            ('PUBLISH', 'Publish Selected'),
            ('ARCHIVE', 'Archive Selected'),
            ('EXPORT', 'Export Selected')
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    def __init__(self, *args, department=None, **kwargs):
        super().__init__(*args, **kwargs)
        if department:
            self.fields['articles'].queryset = Article.objects.filter(department=department)