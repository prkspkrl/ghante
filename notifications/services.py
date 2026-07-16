from django.core.mail import send_mail
from django.template.loader import render_to_string

from .models import Notification


def notify_booking_status(booking, new_status):
    """Create in-app notification and send email when booking status changes."""
    worker = booking.worker
    customer_email = booking.customer_email

    status_labels = {
        'accepted': ('Accepted', 'Your booking has been accepted!'),
        'rejected': ('Rejected', 'Your booking has been declined.'),
        'completed': ('Completed', 'Your booking has been marked as completed.'),
    }

    if new_status not in status_labels:
        return

    label, action_text = status_labels[new_status]

    title = f'Booking {label} by {worker.name}'
    message = (
        f'Hello {booking.customer_name},\n\n'
        f'{action_text}\n\n'
        f'Worker: {worker.name} ({worker.skill})\n'
        f'Date: {booking.preferred_date}\n'
    )
    if booking.preferred_time:
        message += f'Time: {booking.preferred_time}\n'
    if booking.response_message:
        message += f'\nMessage from {worker.name}:\n{booking.response_message}\n'

    Notification.objects.create(
        recipient_email=customer_email,
        title=title,
        message=message,
    )

    try:
        send_mail(
            subject=title,
            message=message,
            from_email=None,
            recipient_list=[customer_email],
            fail_silently=True,
        )
    except Exception:
        pass
