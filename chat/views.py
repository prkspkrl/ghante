import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from profiles.models import WorkerProfile

from .models import ChatMessage, TypingStatus
from notifications.services import notify_new_message

ALLOWED_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/jpg', 'image/gif', 'image/webp']
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB


def chat_with_worker(request, pk):
    worker = get_object_or_404(WorkerProfile, pk=pk)

    if not request.user.is_authenticated:
        messages.warning(request, 'Please login first to chat with workers.')
        return redirect('login')

    if request.method == 'POST':
        message = request.POST.get('message', '').strip()
        image = request.FILES.get('image')

        if not message and not image:
            messages.error(request, 'Message or image required.')
            return redirect('chat_worker', pk=worker.pk)

        sender_name = ''
        if hasattr(request.user, 'profile'):
            sender_name = getattr(request.user.profile, 'full_name', '') or ''
        if not sender_name:
            sender_name = request.user.get_full_name() or request.user.username

        msg_type = 'text'
        if image:
            if image.content_type not in ALLOWED_IMAGE_TYPES:
                messages.error(request, 'Image must be JPG, PNG, GIF, or WebP.')
                return redirect('chat_worker', pk=worker.pk)
            if image.size > MAX_IMAGE_SIZE:
                messages.error(request, 'Image must be under 5MB.')
                return redirect('chat_worker', pk=worker.pk)
            msg_type = 'image'

        ChatMessage.objects.create(
            worker=worker,
            sender=request.user,
            sender_name=sender_name,
            message=message,
            message_type=msg_type,
            image=image,
        )

        TypingStatus.objects.filter(user=request.user, worker=worker).update(is_typing=False)

        chat_msg = ChatMessage.objects.filter(worker=worker, sender=request.user).order_by('-sent_at').first()
        if chat_msg:
            notify_new_message(chat_msg)

        return redirect('chat_worker', pk=worker.pk)

    ChatMessage.objects.filter(
        worker=worker,
    ).exclude(sender=request.user).filter(
        is_read=False,
    ).update(is_read=True, read_at=timezone.now())

    chat_messages = ChatMessage.objects.filter(
        worker=worker,
    ).order_by('sent_at')

    return render(request, 'chat/chat.html', {
        'worker': worker,
        'chat_messages': chat_messages,
    })


def chat_messages_json(request, pk):
    worker = get_object_or_404(WorkerProfile, pk=pk)
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'unauthorized'}, status=401)

    is_worker_owner = worker.user == request.user
    has_chatted = ChatMessage.objects.filter(worker=worker, sender=request.user).exists()
    if not is_worker_owner and not has_chatted:
        return JsonResponse({'error': 'forbidden'}, status=403)

    last_id = request.GET.get('last_id', 0)
    new_msgs = ChatMessage.objects.filter(
        worker=worker, id__gt=last_id,
    ).order_by('sent_at')

    data = []
    for m in new_msgs:
        data.append({
            'id': m.id,
            'sender_name': m.sender_name,
            'message': m.message,
            'message_type': m.message_type,
            'image_url': m.image.url if m.image else None,
            'sent_at': m.sent_at.strftime('%b %d, %H:%M'),
            'is_mine': m.sender_id == request.user.pk,
            'is_read': m.is_read,
        })

    read_msgs = []
    for m in new_msgs:
        if m.sender_id != request.user.pk and not m.is_read:
            read_msgs.append(m.id)

    if read_msgs:
        ChatMessage.objects.filter(id__in=read_msgs).update(is_read=True, read_at=timezone.now())

    return JsonResponse({'messages': data, 'read_ids': read_msgs})


@login_required
def mark_read_json(request, pk):
    worker = get_object_or_404(WorkerProfile, pk=pk)
    ChatMessage.objects.filter(
        worker=worker,
    ).exclude(sender=request.user).filter(
        is_read=False,
    ).update(is_read=True, read_at=timezone.now())
    return JsonResponse({'status': 'ok'})


@login_required
def typing_json(request, pk):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=400)

    worker = get_object_or_404(WorkerProfile, pk=pk)
    try:
        data = json.loads(request.body)
        is_typing = data.get('is_typing', False)
    except (json.JSONDecodeError, AttributeError):
        is_typing = False

    TypingStatus.objects.update_or_create(
        user=request.user,
        worker=worker,
        defaults={'is_typing': is_typing, 'updated_at': timezone.now()},
    )
    return JsonResponse({'status': 'ok'})


@login_required
def typing_status_json(request, pk):
    worker = get_object_or_404(WorkerProfile, pk=pk)
    typing_users = TypingStatus.objects.filter(
        worker=worker,
        is_typing=True,
        updated_at__gte=timezone.now() - timezone.timedelta(seconds=10),
    ).exclude(user=request.user).select_related('user')

    typers = [t.user.get_full_name() or t.user.username for t in typing_users]
    return JsonResponse({'typing': typers})


@login_required
def worker_inbox(request):
    profile = WorkerProfile.objects.filter(user=request.user).first()
    if not profile:
        return redirect('customer_inbox')

    from django.db.models import Max, Q

    conversations = (
        ChatMessage.objects
        .filter(worker=profile)
        .exclude(sender=request.user)
        .exclude(sender__isnull=True)
        .values('sender')
        .annotate(last_time=Max('sent_at'))
        .order_by('-last_time')
    )

    conv_list = []
    seen_senders = set()
    for conv in conversations:
        sender_id = conv['sender']
        if sender_id in seen_senders:
            continue
        seen_senders.add(sender_id)

        sender_user = User.objects.filter(pk=sender_id).first()
        if not sender_user:
            continue

        sender_name = (
            ChatMessage.objects
            .filter(worker=profile, sender=sender_user)
            .order_by('-sent_at')
            .values_list('sender_name', flat=True)
            .first()
        ) or sender_user.username

        last_msg = (
            ChatMessage.objects
            .filter(worker=profile, sender=sender_user)
            .order_by('-sent_at')
            .first()
        )
        unread = (
            ChatMessage.objects
            .filter(worker=profile, sender=sender_user, is_read=False)
            .count()
        )
        conv_list.append({
            'sender': sender_id,
            'sender_name': sender_name,
            'last_message': last_msg.message if last_msg else '',
            'last_message_type': last_msg.message_type if last_msg else 'text',
            'last_time': conv['last_time'],
            'unread': unread,
        })

    return render(request, 'chat/inbox.html', {
        'profile': profile,
        'conversations': conv_list,
    })


@login_required
def worker_chat_reply(request, pk):
    profile = WorkerProfile.objects.filter(user=request.user).first()
    if not profile:
        messages.error(request, 'You need a worker profile to access chat.')
        return redirect('home')

    sender_user = get_object_or_404(User, pk=pk)
    sender_name = ''
    if hasattr(sender_user, 'profile'):
        sender_name = getattr(sender_user.profile, 'full_name', '') or ''
    if not sender_name:
        sender_name = sender_user.get_full_name() or sender_user.username

    if request.method == 'POST':
        message = request.POST.get('message', '').strip()
        image = request.FILES.get('image')

        if not message and not image:
            messages.error(request, 'Message or image required.')
            return redirect('worker_chat_reply', pk=pk)

        worker_name = ''
        if hasattr(request.user, 'profile'):
            worker_name = getattr(request.user.profile, 'full_name', '') or ''
        if not worker_name:
            worker_name = profile.name or request.user.username

        msg_type = 'text'
        if image:
            if image.content_type not in ALLOWED_IMAGE_TYPES:
                messages.error(request, 'Image must be JPG, PNG, GIF, or WebP.')
                return redirect('worker_chat_reply', pk=pk)
            if image.size > MAX_IMAGE_SIZE:
                messages.error(request, 'Image must be under 5MB.')
                return redirect('worker_chat_reply', pk=pk)
            msg_type = 'image'

        ChatMessage.objects.create(
            worker=profile,
            sender=request.user,
            sender_name=worker_name,
            message=message,
            message_type=msg_type,
            image=image,
        )

        TypingStatus.objects.filter(user=request.user, worker=profile).update(is_typing=False)
        chat_msg = ChatMessage.objects.filter(worker=profile, sender=request.user).order_by('-sent_at').first()
        if chat_msg:
            notify_new_message(chat_msg)
        return redirect('worker_chat_reply', pk=pk)

    ChatMessage.objects.filter(
        worker=profile,
        sender=sender_user,
        is_read=False,
    ).update(is_read=True, read_at=timezone.now())

    chat_messages = ChatMessage.objects.filter(
        worker=profile,
    ).filter(
        Q(sender=sender_user) | Q(sender=request.user)
    ).order_by('sent_at')

    return render(request, 'chat/worker_reply.html', {
        'profile': profile,
        'other_user': sender_user,
        'sender_name': sender_name,
        'chat_messages': chat_messages,
    })


@login_required
def worker_chat_json(request, pk):
    profile = WorkerProfile.objects.filter(user=request.user).first()
    if not profile:
        return JsonResponse({'error': 'unauthorized'}, status=401)

    sender_user = get_object_or_404(User, pk=pk)
    last_id = request.GET.get('last_id', 0)

    new_msgs = ChatMessage.objects.filter(
        worker=profile, id__gt=last_id,
    ).filter(
        Q(sender=sender_user) | Q(sender=request.user)
    ).order_by('sent_at')

    data = []
    read_ids = []
    for m in new_msgs:
        data.append({
            'id': m.id,
            'sender_name': m.sender_name,
            'message': m.message,
            'message_type': m.message_type,
            'image_url': m.image.url if m.image else None,
            'sent_at': m.sent_at.strftime('%b %d, %H:%M'),
            'is_mine': m.sender_id == request.user.pk,
            'is_read': m.is_read,
        })
        if m.sender_id != request.user.pk and not m.is_read:
            read_ids.append(m.id)

    if read_ids:
        ChatMessage.objects.filter(id__in=read_ids).update(is_read=True, read_at=timezone.now())

    return JsonResponse({'messages': data, 'read_ids': read_ids})


@login_required
def customer_inbox(request):
    from django.db.models import Max, Q

    conversations = (
        ChatMessage.objects
        .filter(Q(sender=request.user))
        .values('worker')
        .annotate(last_time=Max('sent_at'))
        .order_by('-last_time')
    )

    conv_list = []
    seen_workers = set()
    for conv in conversations:
        worker_id = conv['worker']
        if worker_id in seen_workers:
            continue
        seen_workers.add(worker_id)

        worker_profile = WorkerProfile.objects.filter(pk=worker_id).first()
        if not worker_profile:
            continue

        last_from_worker = (
            ChatMessage.objects
            .filter(worker=worker_profile)
            .exclude(sender=request.user)
            .order_by('-sent_at')
            .first()
        )
        last_from_customer = (
            ChatMessage.objects
            .filter(worker=worker_profile, sender=request.user)
            .order_by('-sent_at')
            .first()
        )
        latest_msg = last_from_worker or last_from_customer
        unread = (
            ChatMessage.objects
            .filter(worker=worker_profile, is_read=False)
            .exclude(sender=request.user)
            .count()
        )
        conv_list.append({
            'worker': worker_profile,
            'last_message': latest_msg.message if latest_msg else '',
            'last_message_type': latest_msg.message_type if latest_msg else 'text',
            'last_time': conv['last_time'],
            'unread': unread,
        })

    return render(request, 'chat/customer_inbox.html', {
        'conversations': conv_list,
    })
