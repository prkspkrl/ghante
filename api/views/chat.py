from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from django.db.models import Q, Max, Count
from chat.models import ChatMessage, TypingStatus
from chat.serializers import ChatMessageSerializer
from profiles.models import WorkerProfile


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def conversation_list(request):
    user = request.user
    # Get all workers this user has chatted with
    sent_worker_ids = ChatMessage.objects.filter(sender=user).values_list('worker_id', distinct=True)
    received_worker_ids = ChatMessage.objects.filter(worker__user=user).values_list('worker_id', distinct=True) if hasattr(user, 'worker_profile') else []
    worker_ids = set(list(sent_worker_ids) + list(received_worker_ids))

    conversations = []
    for worker_id in worker_ids:
        worker = WorkerProfile.objects.filter(pk=worker_id).first()
        if not worker:
            continue
        messages = ChatMessage.objects.filter(
            Q(sender=user, worker=worker) | Q(worker=worker, worker__user=user)
        )
        last = messages.order_by('-sent_at').first()
        unread = messages.filter(is_read=False).exclude(sender=user).count()
        conversations.append({
            'worker_id': worker.pk,
            'worker_name': worker.name,
            'worker_photo_url': worker.photo.url if worker.photo else None,
            'last_message': last.message if last else '',
            'last_message_time': last.sent_at if last else None,
            'unread_count': unread,
        })

    conversations.sort(key=lambda x: x['last_message_time'] or '', reverse=True)
    return Response(conversations)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def chat_messages(request, worker_id):
    worker = WorkerProfile.objects.filter(pk=worker_id).first()
    if not worker:
        return Response({'error': 'Worker not found'}, status=status.HTTP_404_NOT_FOUND)

    user = request.user

    if request.method == 'GET':
        messages = ChatMessage.objects.filter(
            Q(sender=user, worker=worker) | Q(worker=worker, worker__user=user)
        ).select_related('sender').order_by('sent_at')
        serializer = ChatMessageSerializer(messages, many=True, context={'request': request})
        return Response(serializer.data)

    # POST - send message
    message_text = request.data.get('message', '')
    message_type = request.data.get('message_type', 'text')
    image = request.FILES.get('image')

    if not message_text and not image:
        return Response({'error': 'Message or image required'}, status=status.HTTP_400_BAD_REQUEST)

    msg = ChatMessage.objects.create(
        worker=worker,
        sender=user,
        sender_name=user.profile.full_name or user.username,
        message=message_text,
        message_type='image' if image else message_type,
        image=image,
    )
    return Response(ChatMessageSerializer(msg, context={'request': request}).data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_typing(request, worker_id):
    worker = WorkerProfile.objects.filter(pk=worker_id).first()
    if not worker:
        return Response({'error': 'Worker not found'}, status=status.HTTP_404_NOT_FOUND)

    is_typing = request.data.get('is_typing', False)
    status_obj, _ = TypingStatus.objects.get_or_create(user=request.user, worker=worker)
    status_obj.is_typing = is_typing
    status_obj.save()
    return Response({'message': 'Typing status updated'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_messages_read(request, worker_id):
    worker = WorkerProfile.objects.filter(pk=worker_id).first()
    if not worker:
        return Response({'error': 'Worker not found'}, status=status.HTTP_404_NOT_FOUND)

    updated = ChatMessage.objects.filter(
        worker=worker, is_read=False
    ).exclude(sender=request.user).update(is_read=True)
    return Response({'messages_read': updated})
