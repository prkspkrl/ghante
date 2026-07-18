from django.urls import path
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from api.views import auth, workers, jobs, bookings, chat, reviews, notifications, favorites, core


@api_view(['GET'])
@permission_classes([AllowAny])
def api_root(request):
    return Response({
        'auth': {
            'register': '/api/auth/register/',
            'login': '/api/auth/login/',
            'logout': '/api/auth/logout/',
            'profile': '/api/auth/profile/',
            'change_password': '/api/auth/change-password/',
            'verify_email': '/api/auth/verify-email/',
            'send_phone_verification': '/api/auth/send-phone-verification/',
            'verify_phone': '/api/auth/verify-phone/',
            'dashboard': '/api/auth/dashboard/',
        },
        'workers': {
            'list': '/api/workers/',
            'detail': '/api/workers/{id}/',
            'create_update': '/api/workers/profile/',
            'toggle_availability': '/api/workers/toggle-availability/',
            'reviews': '/api/workers/{id}/reviews/',
        },
        'jobs': {
            'my_jobs': '/api/jobs/',
            'browse': '/api/jobs/browse/',
            'detail': '/api/jobs/{id}/',
            'apply': '/api/jobs/{id}/apply/',
            'status': '/api/jobs/{id}/status/',
            'photos': '/api/jobs/{id}/photos/',
            'accept_application': '/api/jobs/applications/{id}/accept/',
            'reject_application': '/api/jobs/applications/{id}/reject/',
        },
        'bookings': {
            'list_create': '/api/bookings/',
            'respond': '/api/bookings/{id}/respond/',
            'cancel': '/api/bookings/{id}/cancel/',
        },
        'chat': {
            'conversations': '/api/chat/',
            'messages': '/api/chat/{worker_id}/',
            'typing': '/api/chat/{worker_id}/typing/',
            'typing_status': '/api/chat/{worker_id}/typing/status/',
            'mark_read': '/api/chat/{worker_id}/read/',
        },
        'reviews': {
            'list_create': '/api/reviews/',
        },
        'notifications': {
            'list': '/api/notifications/',
            'unread_count': '/api/notifications/unread-count/',
            'mark_read': '/api/notifications/{id}/read/',
            'mark_all_read': '/api/notifications/read-all/',
        },
        'favorites': {
            'list': '/api/favorites/',
            'toggle': '/api/favorites/{worker_id}/toggle/',
        },
        'discover': {
            'search_suggestions': '/api/search/suggestions/',
            'global_search': '/api/search/',
            'categories': '/api/services/',
            'service_detail': '/api/services/{skill}/',
            'popular_projects': '/api/projects/',
            'project_detail': '/api/projects/{slug}/',
        },
    })


urlpatterns = [
    path('', api_root, name='api_root'),

    # Auth
    path('auth/register/', auth.register, name='api_register'),
    path('auth/login/', auth.login, name='api_login'),
    path('auth/logout/', auth.logout, name='api_logout'),
    path('auth/profile/', auth.profile, name='api_profile'),
    path('auth/change-password/', auth.change_password, name='api_change_password'),
    path('auth/verify-email/', auth.verify_email, name='api_verify_email'),
    path('auth/send-phone-verification/', auth.send_phone_verification, name='api_send_phone_verification'),
    path('auth/verify-phone/', auth.verify_phone, name='api_verify_phone'),
    path('auth/dashboard/', auth.dashboard_stats, name='api_dashboard_stats'),

    # Workers
    path('workers/', workers.WorkerListView.as_view(), name='api_worker_list'),
    path('workers/<int:pk>/', workers.WorkerDetailView.as_view(), name='api_worker_detail'),
    path('workers/profile/', workers.worker_create_or_update, name='api_worker_create_update'),
    path('workers/toggle-availability/', workers.worker_toggle_availability, name='api_worker_toggle_availability'),

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
    path('bookings/<int:pk>/cancel/', workers.cancel_booking, name='api_cancel_booking'),

    # Chat
    path('chat/', chat.conversation_list, name='api_conversation_list'),
    path('chat/<int:worker_id>/', chat.chat_messages, name='api_chat_messages'),
    path('chat/<int:worker_id>/typing/', chat.update_typing, name='api_chat_typing'),
    path('chat/<int:worker_id>/typing/status/', chat.typing_status, name='api_chat_typing_status'),
    path('chat/<int:worker_id>/read/', chat.mark_messages_read, name='api_chat_read'),

    # Reviews
    path('reviews/', reviews.ReviewListCreateView.as_view(), name='api_review_list_create'),
    path('workers/<int:worker_id>/reviews/', reviews.WorkerReviewsPublicView.as_view(), name='api_worker_reviews'),

    # Notifications
    path('notifications/', notifications.notification_list, name='api_notification_list'),
    path('notifications/unread-count/', notifications.notification_unread_count, name='api_notification_unread_count'),
    path('notifications/<int:pk>/read/', notifications.mark_read, name='api_notification_read'),
    path('notifications/read-all/', notifications.mark_all_read, name='api_notification_read_all'),

    # Favorites
    path('favorites/', favorites.favorite_list, name='api_favorite_list'),
    path('favorites/<int:worker_id>/toggle/', favorites.toggle_favorite, name='api_toggle_favorite'),

    # Discover / Core
    path('search/', core.global_search, name='api_global_search'),
    path('search/suggestions/', core.search_suggestions, name='api_search_suggestions'),
    path('services/', core.service_categories, name='api_service_categories'),
    path('services/<str:skill>/', core.service_detail, name='api_service_detail'),
    path('projects/', core.popular_projects, name='api_popular_projects'),
    path('projects/<str:slug>/', core.project_detail, name='api_project_detail'),
]
