from django.urls import path
from . import views

app_name = 'journal_app'

urlpatterns = [
    path('<slug:dept_slug>/', views.department_home, name='department_home'),
    path('<slug:dept_slug>/submit/', views.department_submit_article, name='department_submit'),
    path('<slug:dept_slug>/dashboard/', views.department_dashboard, name='department_dashboard'),
    path('<slug:dept_slug>/article/<int:article_id>/', views.department_article_detail, name='department_article_detail'),
    path('<slug:dept_slug>/article/<int:article_id>/reviews/', views.manage_reviews, name='manage_reviews'),
    path('<slug:dept_slug>/settings/', views.department_settings, name='department_settings'),
]