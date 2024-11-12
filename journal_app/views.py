from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import ListView, DetailView
from django.core.exceptions import PermissionDenied
from .models import Article

class ArticleListView(ListView):
    model = Article
    template_name = 'journal_app/article_list.html'
    context_object_name = 'articles'
    paginate_by = 10

    def get_queryset(self):
        return Article.objects.filter(status='PUBLISHED').order_by('-publication_date')

class ArticleDetailView(DetailView):
    model = Article
    template_name = 'journal_app/article_detail.html'
    context_object_name = 'article'

    def get_queryset(self):
        if self.request.user.is_authenticated and self.request.user.profile.role in ['EDITOR', 'ADMIN']:
            return Article.objects.all()
        return Article.objects.filter(status='PUBLISHED')

@login_required
def submit_article(request):
    if request.method == 'POST':
        form = ArticleSubmissionForm(request.POST, request.FILES)
        if form.is_valid():
            article = form.save(commit=False)
            article.author = request.user
            article.status = 'SUBMITTED'
            article.save()
            messages.success(request, 'Article submitted successfully!')
            return redirect('article_detail', pk=article.pk)
    else:
        form = ArticleSubmissionForm()
    return render(request, 'journal_app/submit_article.html', {'form': form})

@login_required
def author_dashboard(request):
    articles = Article.objects.filter(author=request.user).order_by('-submission_date')
    return render(request, 'journal_app/author_dashboard.html', {'articles': articles})