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
        from profiles.models import WorkerProfile
        from chat.models import ChatMessage
        from django.db.models import Count

        worker_profile = WorkerProfile.objects.filter(user=request.user).first()
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
