from django.urls import path

from . import views


urlpatterns = [
    path('', views.worker_list, name='worker_list'),
    path('<int:pk>/', views.worker_detail, name='worker_detail'),
    path('create/', views.worker_create, name='worker_create'),
    path('<int:pk>/edit/', views.worker_edit, name='worker_edit'),
    path('bookings/', views.worker_bookings, name='worker_bookings'),
    path('bookings/<int:pk>/action/', views.booking_action, name='booking_action'),
    path('my-bookings/', views.customer_bookings, name='customer_bookings'),
    path('my-bookings/<int:pk>/cancel/', views.cancel_booking, name='cancel_booking'),
]
