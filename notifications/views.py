from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST

from .models import Notification


@login_required
def notification_list(request):
    """Show notifications for the logged-in user's email and mark all as read."""
    notifications = Notification.objects.filter(
        recipient_email=request.user.email,
    ).order_by('-created_at')

    # Mark all as read when user opens the page
    notifications.filter(is_read=False).update(is_read=True)

    return render(request, 'notifications/notification_list.html', {
        'notifications': notifications,
    })


@require_POST
@login_required
def notification_mark_read(request, pk):
    notification = get_object_or_404(Notification, pk=pk, recipient_email=request.user.email)
    notification.is_read = True
    notification.save()
    return redirect('notification_list')


@require_POST
@login_required
def notification_mark_all_read(request):
    Notification.objects.filter(
        recipient_email=request.user.email, is_read=False,
    ).update(is_read=True)
    return redirect('notification_list')


def notification_count_api(request):
    """Return unread count for a given email (JSON-friendly)."""
    from django.http import JsonResponse
    email = request.GET.get('email', '').strip()
    if not email:
        return JsonResponse({'count': 0})
    count = Notification.objects.filter(
        recipient_email=email, is_read=False,
    ).count()
    return JsonResponse({'count': count})
