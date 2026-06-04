"""
App-level URL configuration for the nova app.

Follows the routing pattern from Lesson 02:
- list / detail with <int:pk>
- create / update / delete CRUD routes
- function-based routes for comment / review / gallery actions
- built-in django.contrib.auth views for login / logout / password reset
"""

from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    # ---- Landing / static pages ------------------------------------------
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),

    # ---- Projects --------------------------------------------------------
    path('projects/', views.ProjectListView.as_view(), name='project-list'),
    path('projects/new/', views.ProjectCreateView.as_view(), name='project-create'),
    path('projects/<int:pk>/', views.ProjectDetailView.as_view(), name='project-detail'),
    path('projects/<int:pk>/edit/', views.ProjectUpdateView.as_view(), name='project-update'),
    path('projects/<int:pk>/delete/', views.ProjectDeleteView.as_view(), name='project-delete'),

    path('projects/<int:pk>/review/', views.add_or_update_project_review, name='project-review'),
    path('reviews/<int:pk>/delete/', views.delete_project_review, name='project-review-delete'),

    path('projects/<int:pk>/comment/', views.add_project_comment, name='project-comment-add'),
    path('project-comments/<int:pk>/edit/', views.edit_project_comment, name='project-comment-edit'),
    path('project-comments/<int:pk>/delete/', views.delete_project_comment, name='project-comment-delete'),

    path('projects/<int:pk>/gallery/add/', views.add_project_image, name='project-image-add'),
    path('project-images/<int:pk>/delete/', views.delete_project_image, name='project-image-delete'),

    # ---- News (blog-style) ------------------------------------------------
    path('news/', views.NewsListView.as_view(), name='news-list'),
    path('news/new/', views.NewsCreateView.as_view(), name='news-create'),
    path('news/<int:pk>/', views.NewsDetailView.as_view(), name='news-detail'),
    path('news/<int:pk>/edit/', views.NewsUpdateView.as_view(), name='news-update'),
    path('news/<int:pk>/delete/', views.NewsDeleteView.as_view(), name='news-delete'),
    path('news/<int:pk>/comment/', views.add_news_comment, name='news-comment-add'),
    path('news-comments/<int:pk>/delete/', views.delete_news_comment, name='news-comment-delete'),

    # ---- Authentication ---------------------------------------------------
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='user/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='user/logout.html'), name='logout'),

    path('password_reset/',
         auth_views.PasswordResetView.as_view(template_name='user/password_reset.html'),
         name='password_reset'),
    path('password_reset/done/',
         auth_views.PasswordResetDoneView.as_view(template_name='user/password_reset_done.html'),
         name='password_reset_done'),
    path('reset/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(template_name='user/password_reset_confirm.html'),
         name='password_reset_confirm'),
    path('reset/done/',
         auth_views.PasswordResetCompleteView.as_view(template_name='user/password_reset_complete.html'),
         name='password_reset_complete'),

    # ---- JSON API endpoints (used by the chatbot widget) ------------------
    path('api/chat/', views.chatbot_api, name='api-chat'),
    path('api/faqs/', views.chatbot_faqs_api, name='api-faqs'),
    path('api/projects/', views.projects_api, name='api-projects'),
]
