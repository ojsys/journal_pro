# urls.py
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views
from django.contrib.auth import views as auth_views

app_name = 'journal_app'

urlpatterns = [
    # Authentication URLs
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('password_change/', auth_views.PasswordChangeView.as_view(), name='password_change'),
    path('password_change/done/', auth_views.PasswordChangeDoneView.as_view(), name='password_change_done'),
    path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),

    # Home and Registration
    path('', views.department_home, name='department_home'),
    path('register/', views.register, name='register'),

    # Department URLs
    path('departments/', views.department_list, name='department_list'),
    path('<slug:dept_slug>/', views.department_detail, name='department_detail'),
    path('<slug:dept_slug>/manage/', views.department_manage, name='department_manage'),
    path('<slug:dept_slug>/dashboard/', views.department_dashboard, name='department_dashboard'),

    # Article URLs
    path('<slug:dept_slug>/submit/', views.article_submit, name='article_submit'),
    path('<slug:dept_slug>/article/<int:article_id>/', views.article_detail, name='article_detail'),
    path('<slug:dept_slug>/article/<int:article_id>/edit/', views.article_edit, name='article_edit'),

    # Review URLs
    path('<slug:dept_slug>/article/<int:article_id>/assign-reviewers/', 
         views.review_assign, name='review_assign'),
    path('<slug:dept_slug>/review/<int:review_id>/submit/', 
         views.review_submit, name='review_submit'),
    path('<slug:dept_slug>/reviews/statistics/', 
         views.review_statistics, name='review_statistics'),

    # Profile URLs
    #path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)