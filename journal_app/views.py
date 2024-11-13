from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.contrib import messages
from django.http import Http404
from .models import Department, Article, Volume, Review
from .forms import ArticleSubmissionForm

def department_home(request, dept_slug):
    """
    Display the home page for a specific department
    """
    department = get_object_or_404(Department, slug=dept_slug)
    
    # Get published articles for this department
    articles = Article.objects.filter(
        department=department,
        status='PUBLISHED'
    ).order_by('-publication_date')
    
    # Pagination
    paginator = Paginator(articles, 10)  # Show 10 articles per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get current volumes for the department's journals
    current_volumes = Volume.objects.filter(
        journal__department=department,
        is_current=True
    )
    
    context = {
        'department': department,
        'articles': page_obj,
        'current_volumes': current_volumes,
    }
    
    return render(request, 'journal_app/department_home.html', context)

@login_required
def department_submit_article(request, dept_slug):
    """
    Handle article submission for a specific department
    """
    department = get_object_or_404(Department, slug=dept_slug)
    
    # Check if user has permission to submit to this department
    if not (request.user.is_superuser or request.user.profile.departments.filter(id=department.id).exists()):
        messages.error(request, "You don't have permission to submit articles to this department.")
        return redirect('department_home', dept_slug=dept_slug)
    
    if request.method == 'POST':
        form = ArticleSubmissionForm(request.POST, request.FILES)
        if form.is_valid():
            article = form.save(commit=False)
            article.department = department
            article.author = request.user
            article.status = 'SUBMITTED'
            article.save()
            
            # Handle many-to-many relationships after saving
            form.save_m2m()
            
            messages.success(request, 'Article submitted successfully!')
            return redirect('department_article_detail', dept_slug=dept_slug, article_id=article.id)
    else:
        form = ArticleSubmissionForm()
    
    context = {
        'department': department,
        'form': form,
    }
    
    return render(request, 'journal_app/submit_article.html', context)

@login_required
def department_dashboard(request, dept_slug):
    """
    Display department-specific dashboard based on user role
    """
    department = get_object_or_404(Department, slug=dept_slug)
    user = request.user
    profile = user.profile
    
    # Check department access permission
    if not (user.is_superuser or profile.departments.filter(id=department.id).exists()):
        messages.error(request, "You don't have access to this department's dashboard.")
        return redirect('department_home', dept_slug=dept_slug)
    
    context = {
        'department': department,
        'my_articles': Article.objects.filter(author=user, department=department)
    }
    
    # Add role-specific content
    if profile.role in ['EDITOR', 'DEPT_ADMIN', 'ADMIN']:
        context.update({
            'submitted_articles': Article.objects.filter(
                department=department,
                status='SUBMITTED'
            ),
            'under_review_articles': Article.objects.filter(
                department=department,
                status='UNDER_REVIEW'
            ),
            'accepted_articles': Article.objects.filter(
                department=department,
                status='ACCEPTED'
            )
        })
    elif profile.role == 'REVIEWER':
        context['review_assignments'] = Review.objects.filter(
            reviewer=user,
            article__department=department,
            is_complete=False
        )
    
    return render(request, 'journal_app/department_dashboard.html', context)

@login_required
def department_article_detail(request, dept_slug, article_id):
    """
    Display article details with department-specific access control
    """
    department = get_object_or_404(Department, slug=dept_slug)
    article = get_object_or_404(Article, id=article_id, department=department)
    user = request.user
    
    # Check access permissions
    if article.status != 'PUBLISHED':
        if not (user.is_superuser or 
                user == article.author or 
                user.profile.departments.filter(id=department.id).exists()):
            raise Http404("Article not found")
    
    context = {
        'department': department,
        'article': article,
        'can_edit': user == article.author or user.profile.role in ['EDITOR', 'DEPT_ADMIN', 'ADMIN'],
        'reviews': article.reviews.all() if user.profile.role in ['EDITOR', 'DEPT_ADMIN', 'ADMIN'] else None
    }
    
    return render(request, 'journal_app/article_detail.html', context)

@login_required
def manage_reviews(request, dept_slug, article_id):
    """
    Handle review assignments and review submissions
    """
    department = get_object_or_404(Department, slug=dept_slug)
    article = get_object_or_404(Article, id=article_id, department=department)
    user = request.user
    
    # Check permissions
    if not user.profile.role in ['EDITOR', 'DEPT_ADMIN', 'ADMIN']:
        messages.error(request, "You don't have permission to manage reviews.")
        return redirect('department_article_detail', dept_slug=dept_slug, article_id=article_id)
    
    if request.method == 'POST':
        # Handle review assignment or review submission
        # Implementation depends on the specific action
        pass
    
    context = {
        'department': department,
        'article': article,
        'current_reviewers': Review.objects.filter(article=article),
        'available_reviewers': User.objects.filter(
            profile__role='REVIEWER',
            profile__departments=department
        )
    }
    
    return render(request, 'journal_app/manage_reviews.html', context)

@login_required
def department_settings(request, dept_slug):
    """
    Manage department-specific settings
    """
    department = get_object_or_404(Department, slug=dept_slug)
    
    # Check if user has admin permissions
    if not request.user.profile.role in ['DEPT_ADMIN', 'ADMIN']:
        messages.error(request, "You don't have permission to manage department settings.")
        return redirect('department_home', dept_slug=dept_slug)
    
    if request.method == 'POST':
        # Handle settings update
        pass
    
    context = {
        'department': department,
        'settings': department.settings,
    }
    
    return render(request, 'journal_app/department_settings.html', context)