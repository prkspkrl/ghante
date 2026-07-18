from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST

from .models import Notification


@login_required
def notification_list(request):
    """Show notifications for the logged-in user and mark all as read."""
    notifications = Notification.objects.filter(
        Q(recipient=request.user) | Q(recipient_email=request.user.email),
    ).order_by('-created_at')

    notifications.filter(is_read=False).update(is_read=True)

    return render(request, 'notifications/notification_list.html', {
        'notifications': notifications,
    })


@require_POST
@login_required
def notification_mark_read(request, pk):
    notification = get_object_or_404(
        Notification,
        Q(recipient=request.user) | Q(recipient_email=request.user.email),
        pk=pk,
    )
    notification.is_read = True
    notification.save()
    return redirect('notification_list')


@require_POST
@login_required
def notification_mark_all_read(request):
    Notification.objects.filter(
        Q(recipient=request.user) | Q(recipient_email=request.user.email),
        is_read=False,
    ).update(is_read=True)
    return redirect('notification_list')


@login_required
def notification_count_api(request):
    """Return unread count for the logged-in user (JSON-friendly)."""
    from django.http import JsonResponse
    count = Notification.objects.filter(
        Q(recipient=request.user) | Q(recipient_email=request.user.email),
        is_read=False,
    ).count()
    return JsonResponse({'count': count})
