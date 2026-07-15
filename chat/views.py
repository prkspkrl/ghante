from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from profiles.models import WorkerProfile

from .models import ChatMessage


def chat_with_worker(request, pk):
    worker = get_object_or_404(WorkerProfile, pk=pk)

    if not request.user.is_authenticated:
        messages.warning(request, 'Please login first to chat with workers.')
        return redirect('login')

    if request.method == 'POST':
        message = request.POST.get('message', '').strip()
        if not message:
            messages.error(request, 'Message cannot be empty.')
            return redirect('chat_worker', pk=worker.pk)
        ChatMessage.objects.create(
            worker=worker,
            sender=request.user,
            sender_name=request.user.profile.full_name or request.user.username,
            message=message,
        )
        return redirect('chat_worker', pk=worker.pk)

    from django.db.models import Q
    worker_user = worker.user
    chat_messages = ChatMessage.objects.filter(
        Q(sender=request.user) | Q(sender=worker_user),
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

    last_id = request.GET.get('last_id', 0)
    from django.db.models import Q
    worker_user = worker.user
    new_msgs = ChatMessage.objects.filter(
        Q(sender=request.user) | Q(sender=worker_user),
        worker=worker, id__gt=last_id,
    ).order_by('sent_at').values('id', 'sender_name', 'message', 'sent_at', 'sender_id')

    data = []
    for m in new_msgs:
        data.append({
            'id': m['id'],
            'sender_name': m['sender_name'],
            'message': m['message'],
            'sent_at': m['sent_at'].strftime('%b %d, %H:%M'),
            'is_mine': m['sender_id'] == request.user.pk,
        })

    return JsonResponse({'messages': data})


@login_required
def worker_inbox(request):
    profile = WorkerProfile.objects.filter(user=request.user).first()
    if not profile:
        messages.error(request, 'You need a worker profile to access inbox.')
        return redirect('home')

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
    sender_name = sender_user.profile.full_name or sender_user.username

    if request.method == 'POST':
        message = request.POST.get('message', '').strip()
        if not message:
            messages.error(request, 'Message cannot be empty.')
            return redirect('worker_chat_reply', pk=pk)
        ChatMessage.objects.create(
            worker=profile,
            sender=request.user,
            sender_name=f'{profile.name} (Worker)',
            message=message,
        )
        return redirect('worker_chat_reply', pk=pk)

    ChatMessage.objects.filter(
        worker=profile,
        sender=sender_user,
        is_read=False,
    ).update(is_read=True)

    from django.db.models import Q
    chat_messages = ChatMessage.objects.filter(
        Q(sender=sender_user) | Q(sender=request.user),
        worker=profile,
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

    from django.db.models import Q
    new_msgs = ChatMessage.objects.filter(
        Q(sender=sender_user) | Q(sender=request.user),
        worker=profile, id__gt=last_id,
    ).order_by('sent_at').values('id', 'sender_name', 'message', 'sent_at', 'sender_id')

    data = []
    for m in new_msgs:
        data.append({
            'id': m['id'],
            'sender_name': m['sender_name'],
            'message': m['message'],
            'sent_at': m['sent_at'].strftime('%b %d, %H:%M'),
            'is_mine': m['sender_id'] == request.user.pk,
        })

    return JsonResponse({'messages': data})


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
            'last_time': conv['last_time'],
            'unread': unread,
        })

    return render(request, 'chat/customer_inbox.html', {
        'conversations': conv_list,
    })
