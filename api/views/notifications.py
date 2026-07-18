from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from django.db.models import Q
from notifications.models import Notification
from notifications.serializers import NotificationSerializer


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def notification_list(request):
    user = request.user
    notifications = Notification.objects.filter(
        Q(recipient=user) | Q(recipient_email=user.email)
    ).distinct()[:50]
    serializer = NotificationSerializer(notifications, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def notification_unread_count(request):
    user = request.user
    count = Notification.objects.filter(
        Q(recipient=user) | Q(recipient_email=user.email),
        is_read=False,
    ).count()
    return Response({'count': count})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_read(request, pk):
    notification = Notification.objects.filter(
        pk=pk, recipient=request.user
    ).first()
    if not notification:
        return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
    notification.is_read = True
    notification.save()
    return Response({'message': 'Marked as read'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_all_read(request):
    user = request.user
    updated = Notification.objects.filter(
        Q(recipient=user) | Q(recipient_email=user.email),
        is_read=False,
    ).update(is_read=True)
    return Response({'messages_read': updated})
