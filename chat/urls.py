from django.urls import path

from . import views

urlpatterns = [
    path('<int:pk>/', views.chat_with_worker, name='chat_worker'),
    path('<int:pk>/json/', views.chat_messages_json, name='chat_messages_json'),
    path('<int:pk>/read/', views.mark_read_json, name='chat_mark_read'),
    path('<int:pk>/typing/', views.typing_json, name='chat_typing'),
    path('<int:pk>/typing-status/', views.typing_status_json, name='chat_typing_status'),
    path('inbox/', views.worker_inbox, name='worker_inbox'),
    path('my-conversations/', views.customer_inbox, name='customer_inbox'),
    path('reply/<int:pk>/', views.worker_chat_reply, name='worker_chat_reply'),
    path('reply/<int:pk>/json/', views.worker_chat_json, name='worker_chat_json'),
]
