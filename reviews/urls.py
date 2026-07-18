from django.urls import path

from . import views

urlpatterns = [
    path('worker/<int:worker_pk>/', views.worker_reviews, name='worker_reviews'),
    path('worker/<int:worker_pk>/leave/', views.leave_review_worker, name='leave_review_worker'),
    path('job/<int:job_pk>/leave/', views.leave_review_customer, name='leave_review_customer'),
]
