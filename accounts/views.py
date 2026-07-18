import secrets

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.core.mail import send_mail
from django.core.signing import BadSignature, Signer
from django.shortcuts import redirect, render
from django.urls import reverse

from .forms import ProfileForm, RegisterForm
from .models import UserProfile


def _get_profile(user):
    profile, _ = UserProfile.objects.get_or_create(
        user=user,
        defaults={
            'role': 'customer',
            'is_customer': True,
        },
    )
    return profile


def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            _send_email_verification(request, user)
            return redirect('account_dashboard')
    else:
        form = RegisterForm(initial={'role': 'customer'})

    return render(request, 'accounts/register.html', {'form': form})


@login_required
def dashboard(request):
    context = {}
    if request.user.is_authenticated:
        from profiles.models import WorkerProfile, Booking
        from jobs.models import Job, JobApplication
        from chat.models import ChatMessage
        from django.db.models import Count

        is_worker = hasattr(request.user, 'profile') and request.user.profile.is_worker
        worker_profile = WorkerProfile.objects.filter(user=request.user).first() if is_worker else None
        if worker_profile:
            unread_conversations = (
                ChatMessage.objects
                .filter(worker=worker_profile, is_read=False)
                .exclude(sender=request.user)
                .values('sender', 'sender_name')
                .annotate(count=Count('id'))
                .order_by('-count')
            )
            total_unread = sum(c['count'] for c in unread_conversations)
            context['unread_conversations'] = list(unread_conversations)
            context['total_unread'] = total_unread
            context['worker_profile'] = worker_profile

        # Customer booking stats
        customer_bookings = Booking.objects.filter(customer_email=request.user.email)
        context['customer_stats'] = {
            'posted': customer_bookings.count(),
            'active': customer_bookings.filter(status__in=['pending', 'accepted']).count(),
            'completed': customer_bookings.filter(status='completed').count(),
            'cancelled': customer_bookings.filter(status__in=['cancelled', 'rejected']).count(),
        }

        # Job stats and recent applications
        my_jobs = Job.objects.filter(customer=request.user)
        job_ids = my_jobs.values_list('id', flat=True)
        recent_applications = (
            JobApplication.objects
            .filter(job_id__in=job_ids)
            .select_related('worker', 'worker__user', 'worker__user__profile', 'job')
            .order_by('-created_at')[:10]
        )
        total_applications = JobApplication.objects.filter(job_id__in=job_ids).count()
        pending_applications = JobApplication.objects.filter(job_id__in=job_ids, status='pending').count()

        context['my_jobs'] = my_jobs
        context['recent_applications'] = recent_applications
        context['total_applications'] = total_applications
        context['pending_applications'] = pending_applications
        context['job_stats'] = {
            'total': my_jobs.count(),
            'open': my_jobs.filter(status='open').count(),
            'assigned': my_jobs.filter(status='assigned').count(),
            'completed': my_jobs.filter(status='completed').count(),
        }

        # Customer bookings list
        context['customer_bookings'] = customer_bookings.order_by('-created_at')[:20]

        # Worker bookings & reviews
        if worker_profile:
            from reviews.models import Review
            worker_bookings = Booking.objects.filter(worker=worker_profile).order_by('-created_at')
            context['worker_bookings'] = worker_bookings[:20]
            context['pending_bookings'] = worker_bookings.filter(status='pending').count()
            context['worker_reviews'] = Review.objects.filter(worker=worker_profile).select_related('reviewer').order_by('-created_at')[:20]

        # Unread messages (customer inbox)
        from django.db.models import Q
        unread_messages = ChatMessage.objects.filter(
            Q(sender=request.user) | Q(worker__user=request.user),
            is_read=False
        ).exclude(sender=request.user).count()
        context['unread_messages'] = unread_messages

        # Unread notifications
        from notifications.models import Notification
        unread_notifications = Notification.objects.filter(recipient=request.user, is_read=False).count()
        context['unread_notifications'] = unread_notifications

    return render(request, 'accounts/dashboard.html', context)


@login_required
def profile(request):
    profile = _get_profile(request.user)
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated.')
            return redirect('account_profile')
    else:
        form = ProfileForm(instance=profile)
    return render(request, 'accounts/profile.html', {'form': form})


@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Password changed.')
            return redirect('account_dashboard')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'accounts/change_password.html', {'form': form})


def _send_email_verification(request, user):
    signer = Signer()
    token = signer.sign(user.email)
    link = request.build_absolute_uri(reverse('verify_email', args=[token]))
    send_mail(
        'Verify your email – Ghantey',
        f'Hi {user.username},\n\nVerify your email by clicking:\n{link}\n',
        settings.DEFAULT_FROM_EMAIL or 'noreply@ghantey.local',
        [user.email],
        fail_silently=True,
    )


def verify_email(request, token):
    signer = Signer()
    try:
        email = signer.unsign(token)
        profile = UserProfile.objects.get(user__email=email)
        profile.email_verified = True
        profile.save(update_fields=['email_verified'])
        return render(request, 'accounts/email_verified.html', {'success': True})
    except (BadSignature, UserProfile.DoesNotExist):
        return render(request, 'accounts/email_verified.html', {'success': False})


@login_required
def send_phone_verification(request):
    profile = _get_profile(request.user)
    code = secrets.randbelow(900000) + 100000
    profile.phone_verification_code = str(code)
    profile.save(update_fields=['phone_verification_code'])
    messages.success(
        request,
        f'Your phone verification code is: {code} (console only for MVP)',
    )
    return redirect('account_dashboard')


@login_required
def verify_phone(request):
    profile = _get_profile(request.user)
    if request.method == 'POST':
        code = request.POST.get('code', '').strip()
        if code and code == profile.phone_verification_code:
            profile.phone_verified = True
            profile.save(update_fields=['phone_verified'])
            messages.success(request, 'Phone verified.')
            return redirect('account_dashboard')
        messages.error(request, 'Invalid code. Try again.')
    return render(request, 'accounts/verify_phone.html')
