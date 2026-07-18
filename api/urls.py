from django.urls import path
from api.views import auth, workers, jobs, bookings, chat, reviews, notifications, favorites

urlpatterns = [
    # Auth
    path('auth/register/', auth.register, name='api_register'),
    path('auth/login/', auth.login, name='api_login'),
    path('auth/logout/', auth.logout, name='api_logout'),
    path('auth/profile/', auth.profile, name='api_profile'),

    # Workers
    path('workers/', workers.WorkerListView.as_view(), name='api_worker_list'),
    path('workers/<int:pk>/', workers.WorkerDetailView.as_view(), name='api_worker_detail'),

    # Jobs
    path('jobs/', jobs.JobListCreateView.as_view(), name='api_job_list_create'),
    path('jobs/browse/', jobs.JobBrowseView.as_view(), name='api_job_browse'),
    path('jobs/<int:pk>/', jobs.JobDetailView.as_view(), name='api_job_detail'),
    path('jobs/<int:pk>/applications/', jobs.JobApplicationsView.as_view(), name='api_job_applications'),
    path('jobs/<int:pk>/apply/', jobs.apply_to_job, name='api_job_apply'),
    path('jobs/<int:pk>/photos/', jobs.JobPhotoUploadView.as_view(), name='api_job_photo_upload'),
    path('jobs/<int:pk>/status/', jobs.update_job_status, name='api_job_status'),
    path('jobs/applications/<int:pk>/accept/', jobs.accept_application, name='api_accept_application'),
    path('jobs/applications/<int:pk>/reject/', jobs.reject_application, name='api_reject_application'),

    # Bookings
    path('bookings/', bookings.BookingListCreateView.as_view(), name='api_booking_list_create'),
    path('bookings/<int:pk>/respond/', bookings.respond_booking, name='api_respond_booking'),

    # Chat
    path('chat/', chat.conversation_list, name='api_conversation_list'),
    path('chat/<int:worker_id>/', chat.chat_messages, name='api_chat_messages'),
    path('chat/<int:worker_id>/typing/', chat.update_typing, name='api_chat_typing'),
    path('chat/<int:worker_id>/read/', chat.mark_messages_read, name='api_chat_read'),

    # Reviews
    path('reviews/', reviews.ReviewListCreateView.as_view(), name='api_review_list_create'),
    path('workers/<int:worker_id>/reviews/', reviews.worker_reviews, name='api_worker_reviews'),

    # Notifications
    path('notifications/', notifications.notification_list, name='api_notification_list'),
    path('notifications/<int:pk>/read/', notifications.mark_read, name='api_notification_read'),
    path('notifications/read-all/', notifications.mark_all_read, name='api_notification_read_all'),

    # Favorites
    path('favorites/', favorites.favorite_list, name='api_favorite_list'),
    path('favorites/<int:worker_id>/toggle/', favorites.toggle_favorite, name='api_toggle_favorite'),
]
