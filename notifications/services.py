from django.core.mail import send_mail
from django.urls import reverse


def _create_notification(recipient, recipient_email, actor, notification_type, title, message, target_url=''):
    """Create an in-app notification and send an email."""
    from .models import Notification

    Notification.objects.create(
        recipient=recipient,
        recipient_email=recipient_email,
        actor=actor,
        notification_type=notification_type,
        title=title,
        message=message,
        target_url=target_url,
    )

    try:
        send_mail(
            subject=title,
            message=message,
            from_email=None,
            recipient_list=[recipient_email],
            fail_silently=True,
        )
    except Exception:
        pass


def notify_booking_status(booking, new_status):
    """Notify customer when booking status changes."""
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

    _create_notification(
        recipient=None,
        recipient_email=customer_email,
        actor=worker.user,
        notification_type='booking',
        title=title,
        message=message,
    )


def notify_new_job(job):
    """Notify workers in the same category when a new job is posted."""
    from profiles.models import WorkerProfile

    workers = WorkerProfile.objects.filter(
        category=job.category, is_available=True,
    ).exclude(user=job.customer)

    title = f'New job: {job.title}'
    message = (
        f'A new job matching your skills has been posted.\n\n'
        f'Title: {job.title}\n'
        f'Category: {job.get_category_display()}\n'
        f'Budget: Rs. {job.budget}\n'
    )
    if job.address:
        message += f'Location: {job.address}\n'
    if job.preferred_date:
        message += f'Date: {job.preferred_date}\n'

    target_url = reverse('job_detail', args=[job.pk])

    for worker in workers:
        if worker.user:
            _create_notification(
                recipient=worker.user,
                recipient_email=worker.user.email,
                actor=job.customer,
                notification_type='job',
                title=title,
                message=message,
                target_url=target_url,
            )


def notify_application_received(application):
    """Notify job owner when a worker applies."""
    job = application.job
    worker = application.worker

    title = f'{worker.name} applied to your job'
    message = (
        f'{worker.name} ({worker.skill}) has applied to your job.\n\n'
        f'Job: {job.title}\n'
    )
    if application.message:
        message += f'Message: {application.message}\n'

    target_url = reverse('job_detail', args=[job.pk])

    _create_notification(
        recipient=job.customer,
        recipient_email=job.customer.email,
        actor=worker.user,
        notification_type='application',
        title=title,
        message=message,
        target_url=target_url,
    )


def notify_application_accepted(application):
    """Notify worker when their application is accepted."""
    job = application.job
    worker = application.worker

    title = f'Application accepted for {job.title}'
    message = (
        f'Your application for "{job.title}" has been accepted!\n\n'
        f'You have been assigned to this job. Check the job details for more information.\n'
    )

    target_url = reverse('job_detail', args=[job.pk])

    _create_notification(
        recipient=worker.user,
        recipient_email=worker.user.email,
        actor=job.customer,
        notification_type='accepted',
        title=title,
        message=message,
        target_url=target_url,
    )


def notify_application_rejected(application):
    """Notify worker when their application is rejected."""
    job = application.job
    worker = application.worker

    title = f'Application not selected for {job.title}'
    message = (
        f'Your application for "{job.title}" was not selected.\n\n'
        f'Don\'t worry, keep applying to other jobs!\n'
    )

    target_url = reverse('job_detail', args=[job.pk])

    _create_notification(
        recipient=worker.user,
        recipient_email=worker.user.email,
        actor=job.customer,
        notification_type='application',
        title=title,
        message=message,
        target_url=target_url,
    )


def notify_new_message(chat_message):
    """Notify the recipient of a new chat message."""
    worker = chat_message.worker
    sender = chat_message.sender

    if not sender:
        return

    # Determine recipient: if sender is the customer, recipient is the worker's user; vice versa
    if sender == (worker.user if worker.user else None):
        # Sender is the worker -> recipient is the customer
        # We don't have a direct FK to the customer on ChatMessage,
        # so we skip email for this case (customer would need to be online)
        return
    else:
        # Sender is the customer -> recipient is the worker
        recipient = worker.user
        if not recipient:
            return

    preview = chat_message.message[:80] + ('...' if len(chat_message.message) > 80 else '')
    title = f'New message from {sender.get_full_name() or sender.username}'
    message = f'{sender.get_full_name() or sender.username} sent you a message.\n\n"{preview}"'

    target_url = reverse('worker_chat_reply', args=[sender.pk]) if recipient == worker.user else reverse('chat_worker', args=[worker.pk])

    _create_notification(
        recipient=recipient,
        recipient_email=recipient.email,
        actor=sender,
        notification_type='message',
        title=title,
        message=message,
        target_url=target_url,
    )


def notify_review_created(review):
    """Notify the reviewed party when a review is submitted."""
    from profiles.models import WorkerProfile

    if review.review_type == 'customer_to_worker':
        worker = review.worker
        if not worker or not worker.user:
            return
        title = f'New review from {review.reviewer.get_full_name() or review.reviewer.username}'
        message = (
            f'You received a {review.rating}/5 star review.\n\n'
            f'"{review.comment}"\n' if review.comment else ''
        )
        target_url = reverse('worker_reviews', args=[worker.pk])
        _create_notification(
            recipient=worker.user,
            recipient_email=worker.user.email,
            actor=review.reviewer,
            notification_type='review',
            title=title,
            message=message,
            target_url=target_url,
        )
    else:
        # Worker reviewing customer — notify the customer
        # We don't have a direct customer user FK on the review, so we skip
        pass


def notify_verification_submitted(verification_request):
    """Notify admin when a verification request is submitted."""
    from django.contrib.auth.models import User

    admins = User.objects.filter(is_staff=True, is_active=True)
    title = f'Verification request from {verification_request.applicant_name}'
    message = (
        f'A new verification request has been submitted.\n\n'
        f'Applicant: {verification_request.applicant_name}\n'
        f'Document: {verification_request.document_type}\n'
    )

    target_url = reverse('admin:verification_verificationrequest_changelist')

    for admin in admins:
        _create_notification(
            recipient=admin,
            recipient_email=admin.email,
            actor=None,
            notification_type='verification',
            title=title,
            message=message,
            target_url=target_url,
        )


def notify_verification_status(verification_request, new_status):
    """Notify applicant when verification is approved or rejected."""
    status_map = {
        'approved': ('Verification approved', 'Your identity has been verified!'),
        'rejected': ('Verification rejected', 'Your verification request was not approved.'),
    }

    if new_status not in status_map:
        return

    label, action_text = status_map[new_status]
    title = f'{label}: {verification_request.applicant_name}'
    message = (
        f'{action_text}\n\n'
        f'Document type: {verification_request.document_type}\n'
    )

    _create_notification(
        recipient=None,
        recipient_email=verification_request.applicant_email if hasattr(verification_request, 'applicant_email') else '',
        actor=None,
        notification_type='verification',
        title=title,
        message=message,
    )
