from django.urls import path
from . import views

urlpatterns = [
    path('', views.admin_dashboard, name='admin_dashboard'),
    path('users/', views.admin_users, name='admin_users'),
    path('users/<int:pk>/', views.admin_user_detail, name='admin_user_detail'),
    path('jobs/', views.admin_jobs, name='admin_jobs'),
    path('jobs/<int:pk>/', views.admin_job_detail, name='admin_job_detail'),
    path('categories/', views.admin_categories, name='admin_categories'),
    path('kyc/', views.admin_kyc, name='admin_kyc'),
    path('reviews/', views.admin_reviews, name='admin_reviews'),
    path('payments/', views.admin_payments, name='admin_payments'),
    path('reports/', views.admin_reports, name='admin_reports'),
]
