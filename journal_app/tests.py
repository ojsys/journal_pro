# tests.py
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.core import mail
from django.utils import timezone
from .models import Department, Article, Review, Profile
import json

class JournalSystemTest(TestCase):
    def setUp(self):
        """Set up test data"""
        # Create test users
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@unijos.edu.ng',
            password='adminpass123'
        )
        self.author_user = User.objects.create_user(
            username='author',
            email='author@unijos.edu.ng',
            password='authorpass123'
        )
        self.reviewer_user = User.objects.create_user(
            username='reviewer',
            email='reviewer@unijos.edu.ng',
            password='reviewerpass123'
        )

        # Create department
        self.department = Department.objects.create(
            name='ENGLISH',
            slug='english',
            description='Department of English',
            email='english@unijos.edu.ng'
        )

        # Create user profiles
        Profile.objects.create(
            user=self.admin_user,
            role='ADMIN',
            institution='University of Jos'
        ).departments.add(self.department)

        Profile.objects.create(
            user=self.author_user,
            role='AUTHOR',
            institution='University of Jos'
        ).departments.add(self.department)

        Profile.objects.create(
            user=self.reviewer_user,
            role='REVIEWER',
            institution='University of Jos'
        ).departments.add(self.department)

        self.client = Client()

    def test_user_registration(self):
        """Test user registration process"""
        registration_data = {
            'username': 'newuser',
            'email': 'newuser@unijos.edu.ng',
            'password1': 'newuserpass123',
            'password2': 'newuserpass123',
            'department': self.department.id,
            'role': 'AUTHOR',
            'institution': 'University of Jos'
        }
        
        response = self.client.post(reverse('register'), registration_data)
        self.assertEqual(response.status_code, 302)  # Redirect after successful registration
        self.assertTrue(User.objects.filter(username='newuser').exists())
        self.assertEqual(len(mail.outbox), 1)  # Verification email sent

    def test_article_submission(self):
        """Test article submission process"""
        self.client.login(username='author', password='authorpass123')
        
        with open('test_file.pdf', 'w') as f:
            f.write('test content')

        submission_data = {
            'title': 'Test Article',
            'abstract': 'This is a test article abstract',
            'keywords': 'test, article, research',
            'manuscript_file': open('test_file.pdf', 'rb'),
            'department': self.department.id
        }
        
        response = self.client.post(
            reverse('article_submit', kwargs={'dept_slug': self.department.slug}),
            submission_data
        )
        self.assertEqual(response.status_code, 302)  # Redirect after successful submission
        self.assertTrue(Article.objects.filter(title='Test Article').exists())

    def test_review_assignment(self):
        """Test review assignment process"""
        self.client.login(username='admin', password='adminpass123')
        
        article = Article.objects.create(
            title='Test Article',
            abstract='Test Abstract',
            author=self.author_user,
            department=self.department,
            status='SUBMITTED'
        )
        
        assignment_data = {
            'reviewers': [self.reviewer_user.id],
            'due_date': timezone.now() + timezone.timedelta(days=30),
            'message_to_reviewers': 'Please review this article'
        }
        
        response = self.client.post(
            reverse('review_assign', kwargs={
                'dept_slug': self.department.slug,
                'article_id': article.id
            }),
            assignment_data
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Review.objects.filter(article=article).exists())

    def test_review_submission(self):
        """Test review submission process"""
        self.client.login(username='reviewer', password='reviewerpass123')
        
        article = Article.objects.create(
            title='Test Article',
            abstract='Test Abstract',
            author=self.author_user,
            department=self.department,
            status='UNDER_REVIEW'
        )
        
        review = Review.objects.create(
            article=article,
            reviewer=self.reviewer_user,
            due_date=timezone.now() + timezone.timedelta(days=30)
        )
        
        review_data = {
            'recommendation': 'ACCEPT',
            'comments_to_editor': 'Good article',
            'comments_to_author': 'Well done'
        }
        
        response = self.client.post(
            reverse('review_submit', kwargs={
                'dept_slug': self.department.slug,
                'review_id': review.id
            }),
            review_data
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Review.objects.get(id=review.id).is_complete)

    def test_email_notifications(self):
        """Test email notification system"""
        article = Article.objects.create(
            title='Test Article',
            abstract='Test Abstract',
            author=self.author_user,
            department=self.department,
            status='SUBMITTED'
        )
        
        # Test submission notification
        self.assertEqual(len(mail.outbox), 1)  # Submission confirmation sent
        self.assertIn('submission', mail.outbox[0].subject.lower())
        
        # Clear mailbox
        mail.outbox = []
        
        # Test review assignment notification
        review = Review.objects.create(
            article=article,
            reviewer=self.reviewer_user,
            due_date=timezone.now() + timezone.timedelta(days=30)
        )
        self.assertEqual(len(mail.outbox), 1)  # Review invitation sent
        self.assertIn('review', mail.outbox[0].subject.lower())

    def test_permissions(self):
        """Test permission-based access control"""
        article = Article.objects.create(
            title='Test Article',
            abstract='Test Abstract',
            author=self.author_user,
            department=self.department,
            status='SUBMITTED'
        )
        
        # Test unauthorized access to review assignment
        self.client.login(username='author', password='authorpass123')
        response = self.client.get(
            reverse('review_assign', kwargs={
                'dept_slug': self.department.slug,
                'article_id': article.id
            })
        )
        self.assertEqual(response.status_code, 403)  # Forbidden
        
        # Test authorized access
        self.client.login(username='admin', password='adminpass123')
        response = self.client.get(
            reverse('review_assign', kwargs={
                'dept_slug': self.department.slug,
                'article_id': article.id
            })
        )
        self.assertEqual(response.status_code, 200)  # Success

    def test_dashboard_views(self):
        """Test dashboard views for different user roles"""
        # Admin dashboard
        self.client.login(username='admin', password='adminpass123')
        response = self.client.get(
            reverse('department_dashboard', kwargs={'dept_slug': self.department.slug})
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('submitted_articles', response.context)
        
        # Author dashboard
        self.client.login(username='author', password='authorpass123')
        response = self.client.get(
            reverse('department_dashboard', kwargs={'dept_slug': self.department.slug})
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('my_articles', response.context)
        
        # Reviewer dashboard
        self.client.login(username='reviewer', password='reviewerpass123')
        response = self.client.get(
            reverse('department_dashboard', kwargs={'dept_slug': self.department.slug})
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('review_assignments', response.context)

    def tearDown(self):
        """Clean up test data"""
        import os
        if os.path.exists('test_file.pdf'):
            os.remove('test_file.pdf')