# views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import JsonResponse, Http404, HttpResponse
from django.core.exceptions import PermissionDenied
import csv
from django.utils import timezone
from datetime import datetime, timedelta
from django.urls import reverse
from django.db.models import Q, Count, Sum
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.auth import login, logout, authenticate
from django.views.decorators.http import require_http_methods

from .notifications import NotificationManager
from .models import (Department, DepartmentSettings, Profile, Journal, Article,
                    ArticleFile, Review, ReviewAttachment, EmailLog, AuditLog)
from .forms import (DepartmentForm, DepartmentSettingsForm, UserRegistrationForm,
                   ProfileForm, JournalForm, ArticleSubmissionForm, ArticleFileForm,
                   ReviewForm, ReviewAssignmentForm, ReviewResponseForm,
                   BulkArticleActionForm)



# Authentication Views
def login(request):
    if request.user.is_authenticated:
        return redirect('journal_app:home')
        
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            next_url = request.GET.get('next', 'journal_app:home')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'registration/login.html')

@require_http_methods(["GET", "POST"])
def logout_view(request):
    if request.method == 'POST':
        logout(request)
        return redirect('login')
    return render(request, 'registration/logout.html')


# def register_view(request):
#     if request.user.is_authenticated:
#         return redirect('journal_app:home')
        
#     if request.method == 'POST':
#         form = UserRegistrationForm(request.POST, request.FILES)
#         if form.is_valid():
#             user = form.save()
#             login(request, user)
#             messages.success(request, 'Registration successful!')
#             return redirect('journal_app:home')
#     else:
#         form = UserRegistrationForm()
    
#     return render(request, 'registration/register.html', {'form': form})


# User Management Views
def register(request):
    """User registration"""
    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST)
        profile_form = ProfileForm(request.POST, request.FILES)
        
        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save()
            profile = profile_form.save(commit=False)
            profile.user = user
            profile.save()
            
            # Add user to selected departments
            departments = user_form.cleaned_data['departments']
            profile.departments.set(departments)
            
            messages.success(request, "Registration successful. Please log in.")
            return redirect('login')
    else:
        user_form = UserRegistrationForm()
        profile_form = ProfileForm()
    
    return render(request, 'journal_app/register.html', {
        'form': user_form,
        'form2': profile_form
    })

############## End Athentication ##################### 

# Department Views

def department_home(request):
    context = {
        'departments': Department.objects.filter(is_active=True),
        'recent_journals': Journal.objects.all().order_by('-created_at')[:6],
        'total_articles': Article.objects.count(),
        'total_authors': Profile.objects.filter(role='AUTHOR').count(),
        'total_citations': Article.objects.aggregate(Sum('citation_count'))['citation_count__sum'] or 0,
        'total_downloads': Article.objects.aggregate(Sum('download_count'))['download_count__sum'] or 0,
    }
    return render(request, 'journal_app/department_home.html', context)


@login_required
def department_list(request):
    """View all departments"""
    departments = Department.objects.filter(is_active=True)
    return render(request, 'journal_app/department_list.html', {
        'departments': departments
    })

@login_required
def department_detail(request, dept_slug):
    """View department details"""
    department = get_object_or_404(Department, slug=dept_slug, is_active=True)
    journals = Journal.objects.filter(department=department, is_active=True)
    recent_articles = Article.objects.filter(
        department=department,
        status='PUBLISHED'
    ).order_by('-publication_date')[:5]
    
    context = {
        'department': department,
        'journals': journals,
        'recent_articles': recent_articles
    }
    return render(request, 'journal_app/department_detail.html', context)

@login_required
def department_manage(request, dept_slug):
    """Manage department settings"""
    if not request.user.profile.role in ['DEPT_ADMIN', 'ADMIN']:
        messages.error(request, "You don't have permission to manage department settings.")
        return redirect('department_detail', dept_slug=dept_slug)
    
    department = get_object_or_404(Department, slug=dept_slug)
    if request.method == 'POST':
        form = DepartmentForm(request.POST, request.FILES, instance=department)
        settings_form = DepartmentSettingsForm(
            request.POST,
            instance=department.settings
        )
        if form.is_valid() and settings_form.is_valid():
            form.save()
            settings_form.save()
            messages.success(request, "Department settings updated successfully.")
            return redirect('department_detail', dept_slug=dept_slug)
    else:
        form = DepartmentForm(instance=department)
        settings_form = DepartmentSettingsForm(instance=department.settings)
    
    return render(request, 'journal_app/department_manage.html', {
        'department': department,
        'form': form,
        'settings_form': settings_form
    })

# Journal Views
@login_required
def journal_list(request, dept_slug):
    """List all journals in a department"""
    department = get_object_or_404(Department, slug=dept_slug)
    journals = Journal.objects.filter(department=department, is_active=True)
    return render(request, 'journal_app/journal_list.html', {
        'department': department,
        'journals': journals
    })

@login_required
def journal_detail(request, dept_slug, journal_slug):
    """View journal details"""
    department = get_object_or_404(Department, slug=dept_slug)
    journal = get_object_or_404(Journal, department=department, slug=journal_slug)
    articles = Article.objects.filter(
        journal=journal,
        status='PUBLISHED'
    ).order_by('-publication_date')
    
    paginator = Paginator(articles, 10)
    page = request.GET.get('page')
    articles = paginator.get_page(page)
    
    return render(request, 'journal_app/journal_detail.html', {
        'department': department,
        'journal': journal,
        'articles': articles
    })

# Article Views
@login_required
def article_submit(request, dept_slug, journal_slug=None):
    """Submit new article"""
    department = get_object_or_404(Department, slug=dept_slug)
    journal = None if not journal_slug else get_object_or_404(
        Journal,
        department=department,
        slug=journal_slug
    )
    
    if request.method == 'POST':
        form = ArticleSubmissionForm(
            request.POST,
            request.FILES,
            department=department
        )
        if form.is_valid():
            article = form.save(commit=False)
            article.author = request.user
            article.department = department
            if journal:
                article.journal = journal
            article.status = 'SUBMITTED'
            article.save()
            form.save_m2m()  # Save many-to-many relationships
            
            if article.save():
                notifier = NotificationManager(request)
                notifier.send_submission_confirmation(article)
                notifier.notify_editors_new_submission(article)

            # Create article files
            if 'supplementary_files' in request.FILES:
                for file in request.FILES.getlist('supplementary_files'):
                    ArticleFile.objects.create(
                        article=article,
                        file=file,
                        file_type='SUPPLEMENT',
                        uploaded_by=request.user
                    )
            
            messages.success(request, "Article submitted successfully.")
            return redirect('article_detail', dept_slug=dept_slug, article_id=article.id)
    else:
        form = ArticleSubmissionForm(department=department)
    
    return render(request, 'journal_app/article_submit.html', {
        'department': department,
        'journal': journal,
        'form': form
    })

@login_required
def article_detail(request, dept_slug, article_id):
    """View article details"""
    department = get_object_or_404(Department, slug=dept_slug)
    article = get_object_or_404(Article, department=department, id=article_id)
    
    # Check permissions
    if article.status != 'PUBLISHED':
        if not (request.user == article.author or
                request.user.profile.role in ['EDITOR', 'DEPT_ADMIN', 'ADMIN']):
            raise Http404("Article not found")
    
    reviews = None
    if request.user.profile.role in ['EDITOR', 'DEPT_ADMIN', 'ADMIN']:
        reviews = article.reviews.all()
    
    return render(request, 'journal_app/article_detail.html', {
        'department': department,
        'article': article,
        'reviews': reviews
    })

@login_required
def article_edit(request, dept_slug, article_id):
    """Edit article"""
    department = get_object_or_404(Department, slug=dept_slug)
    article = get_object_or_404(Article, department=department, id=article_id)
    
    # Check permissions
    if not (request.user == article.author or
            request.user.profile.role in ['EDITOR', 'DEPT_ADMIN', 'ADMIN']):
        messages.error(request, "You don't have permission to edit this article.")
        return redirect('article_detail', dept_slug=dept_slug, article_id=article_id)
    
    if request.method == 'POST':
        form = ArticleSubmissionForm(
            request.POST,
            request.FILES,
            instance=article,
            department=department
        )
        if form.is_valid():
            article = form.save()
            messages.success(request, "Article updated successfully.")
            return redirect('article_detail', dept_slug=dept_slug, article_id=article.id)
    else:
        form = ArticleSubmissionForm(instance=article, department=department)
    
    return render(request, 'journal_app/article_edit.html', {
        'department': department,
        'article': article,
        'form': form
    })

# Review Views
@login_required
def review_assign(request, dept_slug, article_id):
    """Assign reviewers to article"""
    department = get_object_or_404(Department, slug=dept_slug)
    article = get_object_or_404(Article, department=department, id=article_id)
    
    if not request.user.profile.role in ['EDITOR', 'DEPT_ADMIN', 'ADMIN']:
        messages.error(request, "You don't have permission to assign reviewers.")
        return redirect('article_detail', dept_slug=dept_slug, article_id=article_id)
    
    if request.method == 'POST':
        form = ReviewAssignmentForm(request.POST, department=department)
        if form.is_valid():
            reviewers = form.cleaned_data['reviewers']
            due_date = form.cleaned_data['due_date']
            message = form.cleaned_data['message_to_reviewers']
            
            for reviewer in reviewers:
                review = Review.objects.create(
                    article=article,
                    reviewer=reviewer,
                    due_date=due_date
                )
                
                # Send email notification
                context = {
                    'reviewer_name': reviewer.get_full_name() or reviewer.username,
                    'article_title': article.title,
                    'due_date': due_date,
                    'message': message,
                    'review_url': request.build_absolute_uri(
                        reverse('review_submit', args=[dept_slug, review.id])
                    )
                }
                
                send_review_notification(reviewer.email, context)
                
            article.status = 'UNDER_REVIEW'
            article.save()
            
            messages.success(request, "Reviewers assigned successfully.")
            return redirect('article_detail', dept_slug=dept_slug, article_id=article_id)
    else:
        form = ReviewAssignmentForm(department=department)
    
    return render(request, 'journal_app/review_assign.html', {
        'department': department,
        'article': article,
        'form': form
    })

@login_required
def review_submit(request, dept_slug, review_id):
    """Submit article review"""
    department = get_object_or_404(Department, slug=dept_slug)
    review = get_object_or_404(Review, id=review_id, article__department=department)
    
    if request.user != review.reviewer:
        messages.error(request, "You don't have permission to submit this review.")
        return redirect('department_dashboard', dept_slug=dept_slug)
    
    if request.method == 'POST':
        form = ReviewForm(request.POST, request.FILES, instance=review)
        if form.is_valid():
            review = form.save()
            messages.success(request, "Review submitted successfully.")
            return redirect('department_dashboard', dept_slug=dept_slug)
    else:
        form = ReviewForm(instance=review)
    
    return render(request, 'journal_app/review_submit.html', {
        'department': department,
        'review': review,
        'form': form
    })



@login_required
def profile_edit(request):
    """Edit user profile"""
    if request.method == 'POST':
        form = ProfileForm(
            request.POST,
            request.FILES,
            instance=request.user.profile
        )
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect('profile_detail')
    else:
        form = ProfileForm(instance=request.user.profile)
    
    return render(request, 'journal_app/profile_edit.html', {
        'form': form
    })

# Dashboard Views
@login_required
def department_dashboard(request, dept_slug):
    """Department dashboard"""
    department = get_object_or_404(Department, slug=dept_slug)
    user = request.user
    
    context = {
        'department': department,
        'submitted_articles': Article.objects.filter(
            department=department,
            author=user
        ).order_by('-submission_date')
    }
    
    if user.profile.role in ['EDITOR', 'DEPT_ADMIN', 'ADMIN']:
        context.update({
            'pending_reviews': Article.objects.filter(
                department=department,
                status='UNDER_REVIEW'
            ),
            'new_submissions': Article.objects.filter(
                department=department,
                status='SUBMITTED'
            ),
            'recent_publications': Article.objects.filter(
                department=department,
                status='PUBLISHED'
            ).order_by('-publication_date')[:5]
        })
    
    elif user.profile.role == 'REVIEWER':
        context['review_assignments'] = Review.objects.filter(
            reviewer=user,
            article__department=department,
            is_complete=False
        )
    
    return render(request, 'journal_app/department_dashboard.html', context)

# Utility Functions
def send_review_notification(email, context):
    """Send email notification for review assignment"""
    subject = f"Review Request: {context['article_title']}"
    message = render_to_string('journal_app/emails/review_request.html', context)
    
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [email],
        html_message=message
    )
    
    # Log the email
    EmailLog.objects.create(
        department=context['department'],
        subject=subject,
        recipient=email,
        content=message,
        status='SENT'
    )

def log_audit(request, action, details):
    """Create audit log entry"""
    AuditLog.objects.create(
        department=request.department,
        user=request.user,
        action=action,
        details=details,
        ip_address=request.META.get('REMOTE_ADDR')
    )



    # Advanced Article Management
@login_required
def article_version_control(request, dept_slug, article_id):
    """Manage article versions and revisions"""
    department = get_object_or_404(Department, slug=dept_slug)
    article = get_object_or_404(Article, department=department, id=article_id)
    
    if not (request.user == article.author or 
            request.user.profile.role in ['EDITOR', 'DEPT_ADMIN', 'ADMIN']):
        raise PermissionDenied
    
    article_files = ArticleFile.objects.filter(article=article).order_by('-version')
    
    if request.method == 'POST':
        form = ArticleFileForm(request.POST, request.FILES)
        if form.is_valid():
            new_version = form.save(commit=False)
            new_version.article = article
            new_version.version = article_files.first().version + 1 if article_files.exists() else 1
            new_version.uploaded_by = request.user
            new_version.save()
            
            messages.success(request, f"Version {new_version.version} uploaded successfully.")
            return redirect('article_version_control', dept_slug=dept_slug, article_id=article_id)
    else:
        form = ArticleFileForm()
    
    return render(request, 'journal_app/article_version_control.html', {
        'department': department,
        'article': article,
        'article_files': article_files,
        'form': form
    })

@login_required
def bulk_article_management(request, dept_slug):
    """Handle bulk operations on articles"""
    department = get_object_or_404(Department, slug=dept_slug)
    
    if not request.user.profile.role in ['EDITOR', 'DEPT_ADMIN', 'ADMIN']:
        raise PermissionDenied
    
    if request.method == 'POST':
        form = BulkArticleActionForm(request.POST, department=department)
        if form.is_valid():
            articles = form.cleaned_data['articles']
            action = form.cleaned_data['action']
            
            if action == 'PUBLISH':
                articles.update(
                    status='PUBLISHED',
                    publication_date=timezone.now()
                )
                messages.success(request, f"{len(articles)} articles published.")
            
            elif action == 'ARCHIVE':
                articles.update(status='ARCHIVED')
                messages.success(request, f"{len(articles)} articles archived.")
            
            elif action == 'EXPORT':
                return export_articles_csv(articles)
    
    else:
        form = BulkArticleActionForm(department=department)
    
    return render(request, 'journal_app/bulk_article_management.html', {
        'department': department,
        'form': form
    })

# Advanced Review Management
@login_required
def review_statistics(request, dept_slug):
    """View review statistics and metrics"""
    department = get_object_or_404(Department, slug=dept_slug)
    
    if not request.user.profile.role in ['EDITOR', 'DEPT_ADMIN', 'ADMIN']:
        raise PermissionDenied
    
    # Calculate review statistics
    stats = {
        'total_reviews': Review.objects.filter(article__department=department).count(),
        'completed_reviews': Review.objects.filter(
            article__department=department,
            is_complete=True
        ).count(),
        'pending_reviews': Review.objects.filter(
            article__department=department,
            is_complete=False
        ).count(),
        'average_review_time': Review.objects.filter(
            article__department=department,
            is_complete=True
        ).aggregate(
            avg_time=Avg(F('completion_date') - F('assigned_date'))
        )['avg_time'],
        'reviewer_stats': Profile.objects.filter(
            departments=department,
            role='REVIEWER'
        ).annotate(
            reviews_completed=Count('user__reviews', filter=Q(user__reviews__is_complete=True)),
            avg_review_time=Avg(
                F('user__reviews__completion_date') - F('user__reviews__assigned_date'),
                filter=Q(user__reviews__is_complete=True)
            )
        )
    }
    
    return render(request, 'journal_app/review_statistics.html', {
        'department': department,
        'stats': stats
    })

# Department Analytics
@login_required
def department_analytics(request, dept_slug):
    """View department analytics and metrics"""
    department = get_object_or_404(Department, slug=dept_slug)
    
    if not request.user.profile.role in ['DEPT_ADMIN', 'ADMIN']:
        raise PermissionDenied
    
    # Time periods for analysis
    today = timezone.now()
    last_month = today - timedelta(days=30)
    last_year = today - timedelta(days=365)
    
    analytics = {
        'submission_trends': Article.objects.filter(
            department=department
        ).extra(
            select={'date': 'date(submission_date)'}
        ).values('date').annotate(
            count=Count('id')
        ).order_by('date'),
        
        'acceptance_rate': {
            'total_submissions': Article.objects.filter(
                department=department,
                submission_date__gte=last_year
            ).count(),
            'accepted': Article.objects.filter(
                department=department,
                status='ACCEPTED',
                submission_date__gte=last_year
            ).count()
        },
        
        'review_metrics': {
            'average_time': Review.objects.filter(
                article__department=department,
                is_complete=True
            ).aggregate(
                avg_time=Avg(F('completion_date') - F('assigned_date'))
            )['avg_time'],
            'reviewer_workload': Profile.objects.filter(
                departments=department,
                role='REVIEWER'
            ).annotate(
                active_reviews=Count(
                    'user__reviews',
                    filter=Q(user__reviews__is_complete=False)
                )
            )
        },
        
        'user_activity': {
            'active_authors': Profile.objects.filter(
                departments=department,
                user__articles__submission_date__gte=last_month
            ).distinct().count(),
            'active_reviewers': Profile.objects.filter(
                departments=department,
                user__reviews__assigned_date__gte=last_month
            ).distinct().count()
        }
    }
    
    return render(request, 'journal_app/department_analytics.html', {
        'department': department,
        'analytics': analytics
    })

# Export Functions
def export_articles_csv(articles):
    """Export articles to CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="articles.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Title', 'Author', 'Status', 'Submission Date',
        'Publication Date', 'Journal', 'DOI'
    ])
    
    for article in articles:
        writer.writerow([
            article.title,
            article.author.get_full_name(),
            article.get_status_display(),
            article.submission_date.strftime('%Y-%m-%d'),
            article.publication_date.strftime('%Y-%m-%d') if article.publication_date else '',
            article.journal.title,
            article.doi or ''
        ])
    
    return response

# API Views for Dynamic Updates
@login_required
def get_article_status(request, dept_slug, article_id):
    """API endpoint for article status updates"""
    department = get_object_or_404(Department, slug=dept_slug)
    article = get_object_or_404(Article, department=department, id=article_id)
    
    if not (request.user == article.author or 
            request.user.profile.role in ['EDITOR', 'DEPT_ADMIN', 'ADMIN']):
        raise PermissionDenied
    
    data = {
        'status': article.get_status_display(),
        'reviews_completed': article.reviews.filter(is_complete=True).count(),
        'reviews_pending': article.reviews.filter(is_complete=False).count(),
        'last_updated': article.updated_at.strftime('%Y-%m-%d %H:%M:%S')
    }
    
    return JsonResponse(data)

@login_required
def get_review_summary(request, dept_slug, article_id):
    """API endpoint for review summary"""
    department = get_object_or_404(Department, slug=dept_slug)
    article = get_object_or_404(Article, department=department, id=article_id)
    
    if not request.user.profile.role in ['EDITOR', 'DEPT_ADMIN', 'ADMIN']:
        raise PermissionDenied
    
    reviews = article.reviews.filter(is_complete=True)
    summary = {
        'accept': reviews.filter(recommendation='ACCEPT').count(),
        'minor_revision': reviews.filter(recommendation='MINOR_REVISION').count(),
        'major_revision': reviews.filter(recommendation='MAJOR_REVISION').count(),
        'reject': reviews.filter(recommendation='REJECT').count()
    }
    
    return JsonResponse(summary)

# Notification System
def send_bulk_notifications(request, dept_slug):
    """Send bulk notifications to department users"""
    department = get_object_or_404(Department, slug=dept_slug)
    
    if not request.user.profile.role in ['DEPT_ADMIN', 'ADMIN']:
        raise PermissionDenied
    
    if request.method == 'POST':
        recipient_role = request.POST.get('recipient_role')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        
        recipients = Profile.objects.filter(
            departments=department,
            role=recipient_role
        ).values_list('user__email', flat=True)
        
        for email in recipients:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=True
            )
            
            # Log the email
            EmailLog.objects.create(
                department=department,
                subject=subject,
                recipient=email,
                content=message,
                status='SENT'
            )
        
        messages.success(request, f"Notifications sent to {len(recipients)} recipients.")
        return redirect('department_dashboard', dept_slug=dept_slug)
    
    return render(request, 'journal_app/send_bulk_notifications.html', {
        'department': department,
        'recipient_roles': Profile.ROLES
    })


