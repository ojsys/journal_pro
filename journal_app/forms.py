from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Article, Profile, Review

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    institution = forms.CharField(max_length=200)
    role = forms.ChoiceField(choices=Profile.ROLES)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'institution', 'role')

class ArticleSubmissionForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = ['title', 'abstract', 'keywords', 'content', 'file']
        widgets = {
            'abstract': forms.Textarea(attrs={'rows': 4}),
            'content': forms.Textarea(attrs={'rows': 8}),
        }