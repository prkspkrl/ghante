from django.db.models import Q

from notifications.models import Notification
from chat.models import ChatMessage
from profiles.models import Booking


def unread_counts(request):
    """Provide unread notification and message counts to all templates."""
    if not request.user.is_authenticated:
        return {}

    email = request.user.email

    # Unread notifications
    unread_notifications = Notification.objects.filter(
        recipient_email=email, is_read=False,
    ).count()

    # Unread chat messages (from workers, not sent by user)
    worker_ids = (
        ChatMessage.objects
        .filter(Q(sender=request.user))
        .values_list('worker_id', flat=True)
        .distinct()
    )
    unread_messages = ChatMessage.objects.filter(
        worker_id__in=worker_ids, is_read=False,
    ).exclude(sender=request.user).count()

    # Pending booking requests (for workers)
    from profiles.models import WorkerProfile
    worker_profile = WorkerProfile.objects.filter(user=request.user).first()
    pending_bookings = 0
    if worker_profile:
        pending_bookings = Booking.objects.filter(
            worker=worker_profile, status='pending',
        ).count()

    return {
        'unread_notifications': unread_notifications,
        'unread_messages': unread_messages,
        'pending_bookings': pending_bookings,
        'total_unread': unread_notifications + unread_messages + pending_bookings,
    }
