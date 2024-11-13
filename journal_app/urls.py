# urls.py
from django.urls import path
from . import views

app_name = 'journal_app'

urlpatterns = [
    # Department URLs
    path('', views.department_list, name='department_list'),
    path('<slug:dept_slug>/', views.department_detail, name='department_detail'),
    path('<slug:dept_slug>/manage/', views.department_manage, name='department_manage'),
    path('<slug:dept_slug>/dashboard/', views.department_dashboard, name='department_dashboard'),
    path('<slug:dept_slug>/analytics/', views.department_analytics, name='department_analytics'),
    
    # Journal URLs
    path('<slug:dept_slug>/journals/', views.journal_list, name='journal_list'),
    path('<slug:dept_slug>/journal/<slug:journal_slug>/', views.journal_detail, name='journal_detail'),
    
    # Article URLs
    path('<slug:dept_slug>/submit/', views.article_submit, name='article_submit'),
    path('<slug:dept_slug>/article/<int:article_id>/', views.article_detail, name='article_detail'),
    path('<slug:dept_slug>/article/<int:article_id>/edit/', views.article_edit, name='article_edit'),
    path('<slug:dept_slug>/article/<int:article_id>/versions/', views.article_version_control, name='article_versions'),
    path('<slug:dept_slug>/articles/bulk/', views.bulk_article_management, name='bulk_article_management'),
    
    # Review URLs
    path('<slug:dept_slug>/article/<int:article_id>/assign-reviewers/', 
         views.review_assign, name='review_assign'),
    path('<slug:dept_slug>/review/<int:review_id>/submit/', 
         views.review_submit, name='review_submit'),
    path('<slug:dept_slug>/reviews/statistics/', views.review_statistics, name='review_statistics'),
    
    # User Management URLs
    path('register/', views.register, name='register'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    
    # API URLs
    path('<slug:dept_slug>/api/article/<int:article_id>/status/', views.get_article_status, name='api_article_status'),
    path('<slug:dept_slug>/api/article/<int:article_id>/review-summary/', views.get_review_summary, name='api_review_summary'),
    
    # Notification URLs
    path('<slug:dept_slug>/notifications/bulk/', views.send_bulk_notifications, name='send_bulk_notifications'),
]