# views/review_system.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from django.db import transaction

from ..models import Article, Review, ReviewAttachment, Department
from ..forms import ReviewAssignmentForm, ReviewForm
from ..notifications import NotificationManager

@login_required
def assign_reviewers(request, dept_slug, article_id):
    """Assign reviewers to an article"""
    department = get_object_or_404(Department, slug=dept_slug)
    article = get_object_or_404(Article, id=article_id, department=department)
    
    # Check if user has permission to assign reviewers
    if not request.user.profile.role in ['EDITOR', 'DEPT_ADMIN', 'ADMIN']:
        raise PermissionDenied
    
    if request.method == 'POST':
        form = ReviewAssignmentForm(request.POST, department=department)
        if form.is_valid():
            try:
                with transaction.atomic():
                    reviewers = form.cleaned_data['reviewers']
                    due_date = form.cleaned_data['due_date']
                    message = form.cleaned_data['message_to_reviewers']
                    
                    notification_manager = NotificationManager(request)
                    
                    for reviewer in reviewers:
                        # Create review assignment
                        review = Review.objects.create(
                            article=article,
                            reviewer=reviewer,
                            due_date=due_date,
                            status='PENDING'
                        )
                        
                        # Send invitation email
                        notification_manager.send_review_invitation(review)
                    
                    # Update article status
                    article.status = 'UNDER_REVIEW'
                    article.save()
                    
                    messages.success(request, f"Successfully assigned {len(reviewers)} reviewers.")
                    return redirect('article_detail', dept_slug=dept_slug, article_id=article_id)
                    
            except Exception as e:
                messages.error(request, f"Error assigning reviewers: {str(e)}")
    else:
        form = ReviewAssignmentForm(department=department)
    
    context = {
        'department': department,
        'article': article,
        'form': form,
        'existing_reviewers': article.reviews.all(),
        'available_reviewers': department.get_available_reviewers()
    }
    
    return render(request, 'journal_app/review/assign_reviewers.html', context)

# views.py
@login_required
def submit_review(request, dept_slug, review_id):
    """Submit a review for an article"""
    department = get_object_or_404(Department, slug=dept_slug)
    review = get_object_or_404(Review, id=review_id, article__department=department)
    
    if request.user != review.reviewer:
        raise PermissionDenied
    
    if review.is_complete:
        messages.warning(request, "This review has already been submitted.")
        return redirect('reviewer_dashboard', dept_slug=dept_slug)
    
    if request.method == 'POST':
        form = ReviewForm(request.POST, request.FILES, instance=review)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Save the review
                    review = form.save(commit=False)
                    review.is_complete = True
                    review.completion_date = timezone.now()
                    review.save()
                    
                    # Handle multiple file uploads
                    uploaded_files = request.FILES.getlist('files')
                    for file in uploaded_files:
                        ReviewAttachment.objects.create(
                            review=review,
                            file=file,
                            description=f"Review attachment - {file.name}",
                            uploaded_by=request.user
                        )
                    
                    # Update reviewer stats and send notifications
                    request.user.profile.increment_reviews_count()
                    notification_manager = NotificationManager(request)
                    notification_manager.notify_review_completed(review)
                    
                    messages.success(
                        request,
                        f"Review submitted successfully with {len(uploaded_files)} attachment(s)."
                    )
                    return redirect('reviewer_dashboard', dept_slug=dept_slug)
                    
            except Exception as e:
                messages.error(request, f"Error submitting review: {str(e)}")
    else:
        form = ReviewForm(instance=review)
    
    context = {
        'department': department,
        'review': review,
        'article': review.article,
        'form': form,
        'existing_files': review.attachments.all()
    }
    
    return render(request, 'journal_app/review/submit_review.html', context)

@login_required
def review_detail(request, dept_slug, review_id):
    """View review details"""
    department = get_object_or_404(Department, slug=dept_slug)
    review = get_object_or_404(Review, id=review_id, article__department=department)
    
    # Check permissions
    if not (request.user == review.reviewer or 
            request.user == review.article.author or
            request.user.profile.role in ['EDITOR', 'DEPT_ADMIN', 'ADMIN']):
        raise PermissionDenied
    
    context = {
        'department': department,
        'review': review,
        'article': review.article,
        'attachments': review.attachments.all()
    }
    
    return render(request, 'journal_app/review/review_detail.html', context)

@login_required
def make_decision(request, dept_slug, article_id):
    """Make editorial decision based on reviews"""
    department = get_object_or_404(Department, slug=dept_slug)
    article = get_object_or_404(Article, id=article_id, department=department)
    
    if not request.user.profile.role in ['EDITOR', 'DEPT_ADMIN', 'ADMIN']:
        raise PermissionDenied
    
    if request.method == 'POST':
        decision = request.POST.get('decision')
        feedback = request.POST.get('feedback')
        
        if decision in ['ACCEPTED', 'REVISION_REQUIRED', 'REJECTED']:
            try:
                with transaction.atomic():
                    article.status = decision
                    if decision == 'ACCEPTED':
                        article.acceptance_date = timezone.now()
                    article.save()
                    
                    # Send notification to author
                    notification_manager = NotificationManager(request)
                    notification_manager.notify_author_decision(article, decision, feedback)
                    
                    messages.success(request, f"Decision '{decision}' has been recorded and author notified.")
                    return redirect('article_detail', dept_slug=dept_slug, article_id=article_id)
                    
            except Exception as e:
                messages.error(request, f"Error recording decision: {str(e)}")
    
    context = {
        'department': department,
        'article': article,
        'completed_reviews': article.reviews.filter(is_complete=True),
        'pending_reviews': article.reviews.filter(is_complete=False)
    }
    
    return render(request, 'journal_app/review/make_decision.html', context)

@login_required
def reviewer_dashboard(request, dept_slug):
    """Dashboard for reviewers"""
    department = get_object_or_404(Department, slug=dept_slug)
    
    if not request.user.profile.role == 'REVIEWER':
        raise PermissionDenied
    
    context = {
        'department': department,
        'pending_reviews': Review.objects.filter(
            reviewer=request.user,
            is_complete=False,
            article__department=department
        ),
        'completed_reviews': Review.objects.filter(
            reviewer=request.user,
            is_complete=True,
            article__department=department
        ),
        'review_statistics': request.user.profile.get_review_statistics()
    }
    
    return render(request, 'journal_app/review/reviewer_dashboard.html', context)

@login_required
def review_summary(request, dept_slug, article_id):
    """View summary of all reviews for an article"""
    department = get_object_or_404(Department, slug=dept_slug)
    article = get_object_or_404(Article, id=article_id, department=department)
    
    if not request.user.profile.role in ['EDITOR', 'DEPT_ADMIN', 'ADMIN']:
        raise PermissionDenied
    
    context = {
        'department': department,
        'article': article,
        'reviews': article.reviews.filter(is_complete=True).select_related('reviewer'),
        'review_summary': article.get_review_summary(),
        'can_make_decision': article.can_make_decision()
    }
    
    return render(request, 'journal_app/review/review_summary.html', context)