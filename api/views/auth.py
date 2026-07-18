import secrets

from django.conf import settings
from django.contrib.auth import authenticate
from django.core.mail import send_mail
from django.core.signing import BadSignature, Signer
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User
from accounts.serializers import RegisterSerializer, LoginSerializer, UserSerializer
from accounts.models import UserProfile


@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    serializer = RegisterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.save()
    token, _ = Token.objects.get_or_create(user=user)

    # Send email verification
    signer = Signer()
    token_str = signer.sign(user.email)
    send_mail(
        'Verify your email – Ghantey',
        f'Hi {user.username},\n\nYour verification token is:\n{token_str}\n',
        settings.DEFAULT_FROM_EMAIL or 'noreply@ghantey.local',
        [user.email],
        fail_silently=True,
    )

    return Response({
        'token': token.key,
        'user': UserSerializer(user).data,
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = authenticate(
        username=serializer.validated_data['username'],
        password=serializer.validated_data['password'],
    )
    if not user:
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
    token, _ = Token.objects.get_or_create(user=user)
    return Response({
        'token': token.key,
        'user': UserSerializer(user).data,
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    request.user.auth_token.delete()
    return Response({'message': 'Logged out'}, status=status.HTTP_200_OK)


@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def profile(request):
    if request.method == 'GET':
        return Response(UserSerializer(request.user).data)

    user = request.user
    data = request.data
    if 'email' in data:
        user.email = data['email']
    if 'first_name' in data:
        user.first_name = data['first_name']
    if 'last_name' in data:
        user.last_name = data['last_name']
    user.save()

    profile_obj = user.profile
    if 'full_name' in data:
        profile_obj.full_name = data['full_name']
    if 'phone_number' in data:
        profile_obj.phone_number = data['phone_number']
    profile_obj.save()

    return Response(UserSerializer(user).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    old_password = request.data.get('old_password', '')
    new_password = request.data.get('new_password', '')
    confirm_password = request.data.get('confirm_password', '')

    if not old_password or not new_password:
        return Response({'error': 'old_password and new_password are required'}, status=status.HTTP_400_BAD_REQUEST)

    if not request.user.check_password(old_password):
        return Response({'error': 'Current password is incorrect'}, status=status.HTTP_400_BAD_REQUEST)

    if new_password != confirm_password:
        return Response({'error': 'New passwords do not match'}, status=status.HTTP_400_BAD_REQUEST)

    if len(new_password) < 6:
        return Response({'error': 'Password must be at least 6 characters'}, status=status.HTTP_400_BAD_REQUEST)

    request.user.set_password(new_password)
    request.user.save()
    return Response({'message': 'Password changed successfully'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_email(request):
    token = request.data.get('token', '')
    if not token:
        return Response({'error': 'Token is required'}, status=status.HTTP_400_BAD_REQUEST)

    signer = Signer()
    try:
        email = signer.unsign(token)
        profile = UserProfile.objects.get(user__email=email)
        profile.email_verified = True
        profile.save(update_fields=['email_verified'])
        return Response({'message': 'Email verified successfully'})
    except (BadSignature, UserProfile.DoesNotExist):
        return Response({'error': 'Invalid or expired token'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_phone_verification(request):
    profile_obj, _ = UserProfile.objects.get_or_create(
        user=request.user,
        defaults={'role': 'customer', 'is_customer': True},
    )
    code = secrets.randbelow(900000) + 100000
    profile_obj.phone_verification_code = str(code)
    profile_obj.save(update_fields=['phone_verification_code'])
    # In production, send via SMS. For MVP, return in response.
    return Response({'message': 'Verification code sent', 'code': code})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_phone(request):
    code = request.data.get('code', '').strip()
    if not code:
        return Response({'error': 'Code is required'}, status=status.HTTP_400_BAD_REQUEST)

    profile_obj, _ = UserProfile.objects.get_or_create(
        user=request.user,
        defaults={'role': 'customer', 'is_customer': True},
    )
    if code == profile_obj.phone_verification_code:
        profile_obj.phone_verified = True
        profile_obj.save(update_fields=['phone_verified'])
        return Response({'message': 'Phone verified successfully'})
    return Response({'error': 'Invalid code'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    from profiles.models import WorkerProfile, Booking
    from jobs.models import Job, JobApplication
    from chat.models import ChatMessage
    from notifications.models import Notification
    from reviews.models import Review
    from django.db.models import Q, Count

    user = request.user
    is_worker = hasattr(user, 'profile') and user.profile.is_worker
    worker_profile = WorkerProfile.objects.filter(user=user).first() if is_worker else None

    # Unread messages
    unread_messages = ChatMessage.objects.filter(
        Q(sender=user) | Q(worker__user=user),
        is_read=False
    ).exclude(sender=user).count()

    # Unread notifications
    unread_notifications = Notification.objects.filter(recipient=user, is_read=False).count()

    # Customer stats
    customer_bookings = Booking.objects.filter(customer_email=user.email)
    job_stats = {}
    my_jobs = Job.objects.filter(customer=user)
    job_stats = {
        'total': my_jobs.count(),
        'open': my_jobs.filter(status='open').count(),
        'assigned': my_jobs.filter(status='assigned').count(),
        'completed': my_jobs.filter(status='completed').count(),
    }

    data = {
        'unread_messages': unread_messages,
        'unread_notifications': unread_notifications,
        'customer_stats': {
            'posted': customer_bookings.count(),
            'active': customer_bookings.filter(status__in=['pending', 'accepted']).count(),
            'completed': customer_bookings.filter(status='completed').count(),
            'cancelled': customer_bookings.filter(status__in=['cancelled', 'rejected']).count(),
        },
        'job_stats': job_stats,
        'role': user.profile.get_role_display() if hasattr(user, 'profile') else 'Customer',
    }

    if worker_profile:
        worker_bookings = Booking.objects.filter(worker=worker_profile)
        data['worker_stats'] = {
            'rating': worker_profile.rating,
            'jobs_count': worker_profile.jobs_count,
            'pending_bookings': worker_bookings.filter(status='pending').count(),
            'total_bookings': worker_bookings.count(),
        }

    return Response(data)
