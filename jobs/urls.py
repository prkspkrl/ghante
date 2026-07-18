from django.urls import path

from . import views

urlpatterns = [
    path('', views.job_list, name='job_list'),
    path('create/', views.job_create, name='job_create'),
    path('my-jobs/', views.my_jobs, name='my_jobs'),
    path('<int:pk>/', views.job_detail, name='job_detail'),
    path('<int:pk>/edit/', views.job_edit, name='job_edit'),
    path('<int:pk>/delete/', views.job_delete, name='job_delete'),
    path('<int:pk>/apply/', views.job_apply, name='job_apply'),
    path('<int:pk>/action/', views.job_action, name='job_action'),
    path('<int:job_pk>/applications/<int:app_pk>/action/', views.application_action, name='application_action'),
]
