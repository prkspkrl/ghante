from django.urls import path

from . import views


urlpatterns = [
    path('', views.worker_list, name='worker_list'),
    path('<int:pk>/', views.worker_detail, name='worker_detail'),
    path('create/', views.worker_create, name='worker_create'),
    path('<int:pk>/edit/', views.worker_edit, name='worker_edit'),
]
