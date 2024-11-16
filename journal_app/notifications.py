# notifications.py

from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.urls import reverse
from .models import EmailLog

class NotificationManager:
    """Handle all email notifications in the system"""
    
    def __init__(self, request=None):
        self.request = request
        self.from_email = settings.DEFAULT_FROM_EMAIL
    
    def _send_email(self, to_email, subject, template_name, context, department):
        """Generic method to send emails"""
        # Render email templates
        html_content = render_to_string(f'journal_app/emails/{template_name}.html', context)
        text_content = render_to_string(f'journal_app/emails/{template_name}.txt', context)
        
        try:
            # Create email message
            msg = EmailMultiAlternatives(
                subject,
                text_content,
                self.from_email,
                [to_email]
            )
            msg.attach_alternative(html_content, "text/html")
            msg.send()
            
            # Log the email
            EmailLog.objects.create(
                department=department,
                subject=subject,
                recipient=to_email,
                content=text_content,
                status='SENT',
                related_article=context.get('article'),
                related_review=context.get('review')
            )
            return True
            
        except Exception as e:
            # Log failed email attempt
            EmailLog.objects.create(
                department=department,
                subject=subject,
                recipient=to_email,
                content=text_content,
                status='FAILED',
                error_message=str(e),
                related_article=context.get('article'),
                related_review=context.get('review')
            )
            return False

    def send_submission_confirmation(self, article):
        """Send confirmation email to author after submission"""
        context = {
            'article': article,
            'author': article.author,
            'department': article.department,
            'article_url': self.request.build_absolute_uri(
                reverse('journal_app:article_detail', args=[
                    article.department.slug,
                    article.id
                ])
            )
        }
        
        return self._send_email(
            article.author.email,
            f'Submission Received: {article.title}',
            'submission_confirmation',
            context,
            article.department
        )

    def notify_editors_new_submission(self, article):
        """Notify department editors about new submission"""
        editors = article.department.get_editors()
        success = True
        
        context = {
            'article': article,
            'author': article.author,
            'department': article.department,
            'review_url': self.request.build_absolute_uri(
                reverse('journal_app:article_detail', args=[
                    article.department.slug,
                    article.id
                ])
            )
        }
        
        for editor in editors:
            success &= self._send_email(
                editor.email,
                f'New Submission: {article.title}',
                'new_submission_editor',
                context,
                article.department
            )
            
        return success

    def send_review_invitation(self, review):
        """Send review invitation to reviewer"""
        context = {
            'review': review,
            'article': review.article,
            'reviewer': review.reviewer,
            'department': review.article.department,
            'due_date': review.due_date,
            'accept_url': self.request.build_absolute_uri(
                reverse('journal_app:review_accept', args=[
                    review.article.department.slug,
                    review.id
                ])
            ),
            'decline_url': self.request.build_absolute_uri(
                reverse('journal_app:review_decline', args=[
                    review.article.department.slug,
                    review.id
                ])
            )
        }
        
        return self._send_email(
            review.reviewer.email,
            f'Review Invitation: {review.article.title}',
            'review_invitation',
            context,
            review.article.department
        )

    def notify_review_completed(self, review):
        """Notify editors about completed review"""
        context = {
            'review': review,
            'article': review.article,
            'reviewer': review.reviewer,
            'department': review.article.department,
            'review_url': self.request.build_absolute_uri(
                reverse('journal_app:review_detail', args=[
                    review.article.department.slug,
                    review.id
                ])
            )
        }
        
        editors = review.article.department.get_editors()
        success = True
        
        for editor in editors:
            success &= self._send_email(
                editor.email,
                f'Review Completed: {review.article.title}',
                'review_completed_editor',
                context,
                review.article.department
            )
            
        return success

    def notify_author_decision(self, article, decision, feedback):
        """Notify author about editorial decision"""
        context = {
            'article': article,
            'author': article.author,
            'department': article.department,
            'decision': decision,
            'feedback': feedback,
            'article_url': self.request.build_absolute_uri(
                reverse('journal_app:article_detail', args=[
                    article.department.slug,
                    article.id
                ])
            )
        }
        
        return self._send_email(
            article.author.email,
            f'Decision on Your Submission: {article.title}',
            'author_decision',
            context,
            article.department
        )

    def send_revision_reminder(self, review):
        """Send reminder to reviewer about upcoming deadline"""
        context = {
            'review': review,
            'article': review.article,
            'reviewer': review.reviewer,
            'department': review.article.department,
            'due_date': review.due_date,
            'review_url': self.request.build_absolute_uri(
                reverse('journal_app:review_submit', args=[
                    review.article.department.slug,
                    review.id
                ])
            )
        }
        
        return self._send_email(
            review.reviewer.email,
            f'Review Reminder: {review.article.title}',
            'review_reminder',
            context,
            review.article.department
        )

    def send_publication_notification(self, article):
        """Notify author about article publication"""
        context = {
            'article': article,
            'author': article.author,
            'department': article.department,
            'article_url': self.request.build_absolute_uri(
                reverse('journal_app:article_detail', args=[
                    article.department.slug,
                    article.id
                ])
            )
        }
        
        return self._send_email(
            article.author.email,
            f'Article Published: {article.title}',
            'publication_notification',
            context,
            article.department
        )

    def send_batch_notification(self, recipients, subject, message, department):
        """Send batch notifications to multiple recipients"""
        success = True
        context = {
            'message': message,
            'department': department
        }
        
        for recipient in recipients:
            success &= self._send_email(
                recipient.email,
                subject,
                'batch_notification',
                context,
                department
            )
            
        return success