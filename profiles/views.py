from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .models import Booking, Favorite, WorkerProfile

ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/jpg']
MAX_SIZE = 1 * 1024 * 1024  # 1MB


def _validate_image(file, field_name):
    if not file:
        return None
    if file.content_type not in ALLOWED_TYPES:
        return f'{field_name} must be JPG or PNG format.'
    if file.size > MAX_SIZE:
        return f'{field_name} must be within 1 MB. Your file is {file.size // (1024 * 1024)} MB.'
    return None


def worker_list(request):
    from django.db.models import Q
    WORKER_Q = Q(user__isnull=True) | Q(user__profile__is_worker=True)

    q = request.GET.get('q', '').strip()
    category = request.GET.get('category', '')
    experience = request.GET.get('experience', '')
    availability = request.GET.get('availability', '')
    rate_min = request.GET.get('rate_min', '')
    rate_max = request.GET.get('rate_max', '')
    distance = request.GET.get('distance', '')
    verified = request.GET.get('verified', '')
    sort = request.GET.get('sort', 'newest')

    workers = WorkerProfile.objects.filter(WORKER_Q, is_available=True)

    if q:
        workers = workers.filter(
            Q(name__icontains=q) |
            Q(skill__icontains=q) |
            Q(location__icontains=q) |
            Q(bio__icontains=q) |
            Q(languages__icontains=q)
        )

    if category:
        workers = workers.filter(category=category)

    if experience:
        workers = workers.filter(experience=experience)

    if availability:
        workers = workers.filter(availability=availability)

    if rate_min:
        try:
            workers = workers.filter(hourly_rate__gte=int(rate_min))
        except ValueError:
            pass

    if rate_max:
        try:
            workers = workers.filter(hourly_rate__lte=int(rate_max))
        except ValueError:
            pass

    if verified:
        workers = workers.filter(is_verified=True)

    if distance and request.user.is_authenticated:
        user_lat = request.user.worker_profile.latitude if hasattr(request.user, 'worker_profile') else None
        user_lng = request.user.worker_profile.longitude if hasattr(request.user, 'worker_profile') else None
        if user_lat and user_lng:
            import math
            nearby_ids = []
            for w in workers:
                if w.latitude and w.longitude:
                    R = 6371
                    dlat = math.radians(w.latitude - user_lat)
                    dlon = math.radians(w.longitude - user_lng)
                    a = (math.sin(dlat / 2) ** 2 +
                         math.cos(math.radians(user_lat)) * math.cos(math.radians(w.latitude)) *
                         math.sin(dlon / 2) ** 2)
                    d = R * 2 * math.asin(math.sqrt(a))
                    if d <= float(distance):
                        nearby_ids.append(w.id)
            if nearby_ids:
                workers = workers.filter(id__in=nearby_ids)
            else:
                workers = workers.none()

    if sort == 'rating':
        workers = workers.order_by('-rating')
    elif sort == 'rate_high':
        workers = workers.order_by('-hourly_rate')
    elif sort == 'rate_low':
        workers = workers.order_by('hourly_rate')
    elif sort == 'jobs':
        workers = workers.order_by('-jobs_count')
    else:
        workers = workers.order_by('-created_at')

    favorited_ids = set()
    if request.user.is_authenticated:
        favorited_ids = set(
            Favorite.objects.filter(user=request.user).values_list('worker_id', flat=True)
        )

    return render(request, 'profiles/worker_list.html', {
        'workers': workers,
        'favorited_ids': favorited_ids,
        'query': q,
        'selected_category': category,
        'selected_experience': experience,
        'selected_availability': availability,
        'rate_min': rate_min,
        'rate_max': rate_max,
        'selected_distance': distance,
        'selected_verified': verified,
        'selected_sort': sort,
        'categories': WorkerProfile.CATEGORY_CHOICES,
        'experience_choices': WorkerProfile.EXPERIENCE_CHOICES,
        'availability_choices': WorkerProfile.AVAILABILITY_CHOICES,
    })


def worker_detail(request, pk):
    worker = get_object_or_404(WorkerProfile, pk=pk, is_available=True)
    from reviews.models import Review
    reviews = Review.objects.filter(
        worker=worker, review_type='customer_to_worker'
    ).select_related('reviewer', 'job')[:5]

    can_review = False
    completed_jobs = []
    if request.user.is_authenticated and worker.user != request.user:
        from jobs.models import Job
        completed_jobs = Job.objects.filter(
            customer=request.user, status='completed'
        ).exclude(
            reviews__reviewer=request.user,
            reviews__worker=worker,
            reviews__review_type='customer_to_worker',
        )
        can_review = completed_jobs.exists()

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        date = request.POST.get('date', '')
        time = request.POST.get('time', '') or None
        description = request.POST.get('description', '').strip()
        if not name or not email or not date or not description:
            messages.error(request, 'Please fill in all required fields.')
            return render(request, 'profiles/worker_detail.html', {'worker': worker})
        if '@' not in email or '.' not in email.split('@')[-1]:
            messages.error(request, 'Please enter a valid email address.')
            return render(request, 'profiles/worker_detail.html', {'worker': worker})
        description = description[:2000]
        name = name[:120]
        Booking.objects.create(
            worker=worker,
            customer_name=name,
            customer_email=email,
            customer_phone=phone,
            preferred_date=date,
            preferred_time=time,
            description=description,
        )
        messages.success(request, f'Booking request sent to {worker.name}! They will respond soon.')
        return redirect('worker_detail', pk=worker.pk)
    return render(request, 'profiles/worker_detail.html', {
        'worker': worker,
        'reviews': reviews,
        'can_review': can_review,
        'completed_jobs': completed_jobs,
    })


_FORM_CTX = {
    'categories': WorkerProfile.CATEGORY_CHOICES,
    'experience_choices': WorkerProfile.EXPERIENCE_CHOICES,
    'availability_choices': WorkerProfile.AVAILABILITY_CHOICES,
}


@login_required
def worker_create(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        skill = request.POST.get('skill', '').strip()
        bio = request.POST.get('bio', '').strip()
        hourly_rate = request.POST.get('hourly_rate', '0')
        location = request.POST.get('location', '').strip()
        lat = request.POST.get('latitude', '')
        lng = request.POST.get('longitude', '')
        category = request.POST.get('category', 'other')
        languages = request.POST.get('languages', '').strip()
        experience = request.POST.get('experience', '')
        availability = request.POST.get('availability', '')
        photo = request.FILES.get('photo')
        citizenship_photo = request.FILES.get('citizenship_photo')
        if not name or not skill:
            messages.error(request, 'Name and skill are required.')
            return render(request, 'profiles/worker_form.html', _FORM_CTX)
        err = _validate_image(photo, 'Profile photo')
        if err:
            messages.error(request, err)
            return render(request, 'profiles/worker_form.html', _FORM_CTX)
        err = _validate_image(citizenship_photo, 'Citizenship photo')
        if err:
            messages.error(request, err)
            return render(request, 'profiles/worker_form.html', _FORM_CTX)
        obj, created = WorkerProfile.objects.update_or_create(
            user=request.user,
            defaults={
                'name': name,
                'skill': skill,
                'bio': bio,
                'hourly_rate': int(hourly_rate) if hourly_rate.isdigit() else 0,
                'location': location,
                'latitude': float(lat) if lat else None,
                'longitude': float(lng) if lng else None,
                'category': category,
                'languages': languages,
                'experience': experience,
                'availability': availability,
                'is_available': True,
            },
        )
        if photo:
            obj.photo = photo
        if citizenship_photo:
            obj.citizenship_photo = citizenship_photo
            obj.is_verified = False
        obj.save()
        messages.success(request, 'Worker profile created!')
        return redirect('worker_detail', pk=obj.pk)
    return render(request, 'profiles/worker_form.html', _FORM_CTX)


@login_required
def worker_edit(request, pk):
    worker = get_object_or_404(WorkerProfile, pk=pk, user=request.user)
    ctx = {'worker': worker, **_FORM_CTX}
    if request.method == 'POST':
        worker.name = request.POST.get('name', worker.name).strip()
        worker.skill = request.POST.get('skill', worker.skill).strip()
        worker.bio = request.POST.get('bio', worker.bio).strip()
        hr = request.POST.get('hourly_rate', str(worker.hourly_rate)).strip()
        worker.hourly_rate = int(hr) if hr.isdigit() else worker.hourly_rate
        worker.location = request.POST.get('location', worker.location).strip()
        lat = request.POST.get('latitude', '')
        lng = request.POST.get('longitude', '')
        if lat:
            worker.latitude = float(lat)
        if lng:
            worker.longitude = float(lng)
        worker.category = request.POST.get('category', worker.category)
        worker.languages = request.POST.get('languages', worker.languages).strip()
        worker.experience = request.POST.get('experience', worker.experience)
        worker.availability = request.POST.get('availability', worker.availability)
        worker.is_available = request.POST.get('is_available') == 'on'
        photo = request.FILES.get('photo')
        citizenship_photo = request.FILES.get('citizenship_photo')
        err = _validate_image(photo, 'Profile photo')
        if err:
            messages.error(request, err)
            return render(request, 'profiles/worker_form.html', ctx)
        err = _validate_image(citizenship_photo, 'Citizenship photo')
        if err:
            messages.error(request, err)
            return render(request, 'profiles/worker_form.html', ctx)
        if photo:
            worker.photo = photo
        if citizenship_photo:
            worker.citizenship_photo = citizenship_photo
            worker.is_verified = False
        worker.save()
        messages.success(request, 'Profile updated.')
        return redirect('worker_detail', pk=worker.pk)
    return render(request, 'profiles/worker_form.html', ctx)


@login_required
def worker_bookings(request):
    profile = WorkerProfile.objects.filter(user=request.user).first()
    if not profile:
        messages.error(request, 'You need a worker profile to view bookings.')
        return redirect('home')

    bookings = Booking.objects.filter(worker=profile).order_by('-created_at')
    return render(request, 'profiles/worker_bookings.html', {
        'profile': profile,
        'bookings': bookings,
    })


@login_required
def booking_action(request, pk):
    profile = WorkerProfile.objects.filter(user=request.user).first()
    if not profile:
        messages.error(request, 'You need a worker profile.')
        return redirect('home')

    booking = get_object_or_404(Booking, pk=pk, worker=profile)

    if request.method == 'POST':
        from notifications.services import notify_booking_status

        action = request.POST.get('action', '')
        response = request.POST.get('response_message', '').strip()

        if action == 'accept':
            booking.status = 'accepted'
            booking.response_message = response
            booking.save()
            notify_booking_status(booking, 'accepted')
            messages.success(request, f'Booking from {booking.customer_name} accepted!')
        elif action == 'reject':
            booking.status = 'rejected'
            booking.response_message = response
            booking.save()
            notify_booking_status(booking, 'rejected')
            messages.success(request, f'Booking from {booking.customer_name} rejected.')
        elif action == 'complete':
            booking.status = 'completed'
            booking.response_message = response
            booking.save()
            notify_booking_status(booking, 'completed')
            messages.success(request, f'Booking from {booking.customer_name} marked as completed.')

    return redirect('worker_bookings')


@login_required
def customer_bookings(request):
    """Show bookings for the logged-in user's email."""
    from notifications.models import Notification
    Notification.objects.filter(
        recipient_email=request.user.email, is_read=False,
    ).update(is_read=True)

    filter_val = request.GET.get('filter', 'all')
    bookings = Booking.objects.filter(
        customer_email=request.user.email,
    ).select_related('worker').order_by('-created_at')
    return render(request, 'profiles/customer_bookings.html', {
        'bookings': bookings,
        'filter': filter_val,
    })


@login_required
def cancel_booking(request, pk):
    """Allow customer to cancel a pending booking."""
    if request.method != 'POST':
        return redirect('customer_bookings')

    booking = get_object_or_404(Booking, pk=pk, customer_email=request.user.email)

    if booking.status != 'pending':
        messages.error(request, 'Only pending bookings can be cancelled.')
        return redirect('customer_bookings')

    booking.status = 'cancelled'
    booking.save()
    messages.success(request, 'Booking cancelled successfully.')
    return redirect('customer_bookings')


@login_required
def toggle_favorite(request, pk):
    """Toggle favorite status for a worker."""
    if request.method != 'POST':
        return redirect('worker_list')

    worker = get_object_or_404(WorkerProfile, pk=pk)
    fav, created = Favorite.objects.get_or_create(user=request.user, worker=worker)
    if not created:
        fav.delete()
        messages.success(request, f'{worker.name} removed from favorites.')
    else:
        messages.success(request, f'{worker.name} added to favorites!')

    referer = request.META.get('HTTP_REFERER', '')
    if referer and referer.startswith(request.build_absolute_uri('/')):
        return redirect(referer)
    return redirect('worker_detail', pk=pk)


@login_required
def favorite_workers(request):
    """Show list of favorited workers."""
    favs = Favorite.objects.filter(user=request.user).select_related('worker')
    workers = [f.worker for f in favs]
    return render(request, 'profiles/favorite_workers.html', {'workers': workers})
