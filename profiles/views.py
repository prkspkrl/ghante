from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .models import Booking, WorkerProfile

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
    workers = WorkerProfile.objects.filter(is_available=True).order_by('-created_at')
    return render(request, 'profiles/worker_list.html', {'workers': workers})


def worker_detail(request, pk):
    worker = get_object_or_404(WorkerProfile, pk=pk, is_available=True)
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
    return render(request, 'profiles/worker_detail.html', {'worker': worker})


@login_required
def worker_create(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        skill = request.POST.get('skill', '').strip()
        bio = request.POST.get('bio', '').strip()
        hourly_rate = request.POST.get('hourly_rate', '0')
        location = request.POST.get('location', '').strip()
        photo = request.FILES.get('photo')
        citizenship_photo = request.FILES.get('citizenship_photo')
        if not name or not skill:
            messages.error(request, 'Name and skill are required.')
            return render(request, 'profiles/worker_form.html')
        err = _validate_image(photo, 'Profile photo')
        if err:
            messages.error(request, err)
            return render(request, 'profiles/worker_form.html')
        err = _validate_image(citizenship_photo, 'Citizenship photo')
        if err:
            messages.error(request, err)
            return render(request, 'profiles/worker_form.html')
        obj, created = WorkerProfile.objects.update_or_create(
            user=request.user,
            defaults={
                'name': name,
                'skill': skill,
                'bio': bio,
                'hourly_rate': int(hourly_rate) if hourly_rate.isdigit() else 0,
                'location': location,
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
    return render(request, 'profiles/worker_form.html')


@login_required
def worker_edit(request, pk):
    worker = get_object_or_404(WorkerProfile, pk=pk, user=request.user)
    if request.method == 'POST':
        worker.name = request.POST.get('name', worker.name).strip()
        worker.skill = request.POST.get('skill', worker.skill).strip()
        worker.bio = request.POST.get('bio', worker.bio).strip()
        hr = request.POST.get('hourly_rate', str(worker.hourly_rate)).strip()
        worker.hourly_rate = int(hr) if hr.isdigit() else worker.hourly_rate
        worker.location = request.POST.get('location', worker.location).strip()
        worker.is_available = request.POST.get('is_available') == 'on'
        photo = request.FILES.get('photo')
        citizenship_photo = request.FILES.get('citizenship_photo')
        err = _validate_image(photo, 'Profile photo')
        if err:
            messages.error(request, err)
            return render(request, 'profiles/worker_form.html', {'worker': worker})
        err = _validate_image(citizenship_photo, 'Citizenship photo')
        if err:
            messages.error(request, err)
            return render(request, 'profiles/worker_form.html', {'worker': worker})
        if photo:
            worker.photo = photo
        if citizenship_photo:
            worker.citizenship_photo = citizenship_photo
            worker.is_verified = False
        worker.save()
        messages.success(request, 'Profile updated.')
        return redirect('worker_detail', pk=worker.pk)
    return render(request, 'profiles/worker_form.html', {'worker': worker})
