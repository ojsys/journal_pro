# forms.py
from django import forms
from django.forms.widgets import FileInput
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import (Department, DepartmentSettings, Profile, Journal, Article, 
                    ArticleFile, Review, ReviewAttachment, CustomUser)

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
    #email = forms.EmailField(required=True)
    departments = forms.ModelMultipleChoiceField(
        queryset=Department.objects.filter(is_active=True),
        widget=forms.CheckboxSelectMultiple,
        required=True
    )
    
    class Meta:
        model = CustomUser
        fields = ['email', 'password1', 'password2', 'first_name', 'last_name']
        widgets = { 
            'email': forms.EmailInput(attrs={'class':'form-control'}), 
            'password1': forms.PasswordInput(attrs={'class':'form-control'}), 
            'password2': forms.PasswordInput(attrs={'class':'form-control'}),
            'first_name': forms.TextInput(attrs={'class':'form-control'}), 
            'last_name': forms.TextInput(attrs={'class':'form-control'})
        }

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

class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result

class ReviewForm(forms.ModelForm):
    files = MultipleFileField(
        label='Attachments',
        required=False,
        widget=MultipleFileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.doc,.docx,.txt'
        })
    )

    class Meta:
        model = Review
        fields = ['recommendation', 'comments_to_editor', 'comments_to_author']
        widgets = {
            'recommendation': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'comments_to_editor': forms.Textarea(attrs={
                'rows': 6,
                'class': 'form-control',
                'required': True,
                'placeholder': 'Enter your confidential comments to the editor'
            }),
            'comments_to_author': forms.Textarea(attrs={
                'rows': 6,
                'class': 'form-control',
                'required': True,
                'placeholder': 'Enter your comments to the author'
            })
        }

    def clean_files(self):
        files = self.cleaned_data.get('files', [])
        if not files:
            return files

        max_size = 10 * 1024 * 1024  # 10MB
        allowed_extensions = ['.pdf', '.doc', '.docx', '.txt']

        for file in files:
            if file.size > max_size:
                raise ValidationError(f'File {file.name} is too large. Maximum size is 10MB.')

            ext = os.path.splitext(file.name)[1].lower()
            if ext not in allowed_extensions:
                raise ValidationError(
                    f'File {file.name} has an invalid extension. Allowed types are: {", ".join(allowed_extensions)}'
                )

        return files


class ReviewAttachmentForm(forms.ModelForm):
    class Meta:
        model = ReviewAttachment
        fields = ['file', 'description']
        widgets = {
            'file': forms.FileInput(attrs={'class': 'form-control'}),
            'description': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Brief description of the file'
                }
            )
        }

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