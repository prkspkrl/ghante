from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .models import Job, JobApplication, JobPhoto
from notifications.services import notify_new_job, notify_application_received, notify_application_accepted, notify_application_rejected

ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/jpg']
MAX_SIZE = 5 * 1024 * 1024  # 5MB


def _haversine(lat1, lon1, lat2, lon2):
    """Calculate distance in km between two points using Haversine formula."""
    import math
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    return R * 2 * math.asin(math.sqrt(a))


def job_list(request):
    q = request.GET.get('q', '').strip()
    category = request.GET.get('category', '')
    budget_min = request.GET.get('budget_min', '')
    budget_max = request.GET.get('budget_max', '')
    distance = request.GET.get('distance', '')
    sort = request.GET.get('sort', 'newest')

    jobs = Job.objects.filter(status='open').select_related('customer')

    if q:
        jobs = jobs.filter(
            Q(title__icontains=q) |
            Q(description__icontains=q) |
            Q(address__icontains=q) |
            Q(category__icontains=q)
        )

    if category:
        jobs = jobs.filter(category=category)

    if budget_min:
        try:
            jobs = jobs.filter(budget__gte=int(budget_min))
        except ValueError:
            pass

    if budget_max:
        try:
            jobs = jobs.filter(budget__lte=int(budget_max))
        except ValueError:
            pass

    if distance and request.user.is_authenticated:
        from profiles.models import WorkerProfile
        worker_profile = WorkerProfile.objects.filter(user=request.user).first()
        if worker_profile and worker_profile.latitude and worker_profile.longitude:
            user_lat = worker_profile.latitude
            user_lng = worker_profile.longitude
            nearby_ids = []
            for job in jobs:
                if job.latitude and job.longitude:
                    d = _haversine(user_lat, user_lng, job.latitude, job.longitude)
                    if d <= float(distance):
                        nearby_ids.append(job.id)
            if nearby_ids:
                jobs = jobs.filter(id__in=nearby_ids)
            else:
                jobs = jobs.none()

    if sort == 'budget_high':
        jobs = jobs.order_by('-budget')
    elif sort == 'budget_low':
        jobs = jobs.order_by('budget')
    elif sort == 'date':
        jobs = jobs.order_by('preferred_date')
    else:
        jobs = jobs.order_by('-created_at')

    return render(request, 'jobs/job_list.html', {
        'jobs': jobs,
        'query': q,
        'selected_category': category,
        'budget_min': budget_min,
        'budget_max': budget_max,
        'selected_distance': distance,
        'selected_sort': sort,
        'categories': Job.CATEGORY_CHOICES,
    })


def job_detail(request, pk):
    job = get_object_or_404(Job, pk=pk)
    is_owner = request.user.is_authenticated and job.customer == request.user
    has_applied = False
    worker_profile = None
    can_review_worker = False
    can_review_customer = False
    has_reviewed_worker = False
    has_reviewed_customer = False
    active_worker = None

    if request.user.is_authenticated and not is_owner:
        from profiles.models import WorkerProfile
        worker_profile = WorkerProfile.objects.filter(user=request.user).first()
        if worker_profile:
            has_applied = JobApplication.objects.filter(job=job, worker=worker_profile).exists()

    accepted_app = JobApplication.objects.filter(job=job, status='accepted').select_related('worker').first()
    if accepted_app:
        active_worker = accepted_app.worker

    if is_owner and job.status in ('assigned', 'in_progress'):
        from reviews.models import Review
        if accepted_app:
            has_reviewed_worker = Review.objects.filter(
                reviewer=request.user, worker=accepted_app.worker, job=job,
                review_type='customer_to_worker'
            ).exists()
            can_review_worker = not has_reviewed_worker

    if request.user.is_authenticated and not is_owner and job.status == 'completed':
        from reviews.models import Review
        from profiles.models import WorkerProfile
        wp = WorkerProfile.objects.filter(user=request.user).first()
        if wp and JobApplication.objects.filter(job=job, worker=wp, status='accepted').exists():
            has_reviewed_customer = Review.objects.filter(
                reviewer=request.user, job=job, review_type='worker_to_customer'
            ).exists()
            can_review_customer = not has_reviewed_customer

    return render(request, 'jobs/job_detail.html', {
        'job': job,
        'is_owner': is_owner,
        'has_applied': has_applied,
        'active_worker': active_worker,
        'can_review_worker': can_review_worker,
        'can_review_customer': can_review_customer,
        'has_reviewed_worker': has_reviewed_worker,
        'has_reviewed_customer': has_reviewed_customer,
    })


@login_required
def job_create(request):
    from profiles.models import WorkerProfile
    CATEGORY_CHOICES = Job.CATEGORY_CHOICES
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        category = request.POST.get('category', 'other')
        if category not in dict(Job.CATEGORY_CHOICES):
            category = 'other'
        address = request.POST.get('address', '').strip()
        budget = request.POST.get('budget', '0')
        hours_needed = request.POST.get('hours_needed', '1')
        preferred_date = request.POST.get('preferred_date', '')
        workers_needed = request.POST.get('workers_needed', '1')
        status = request.POST.get('status', 'draft')
        if status not in ('draft', 'open'):
            status = 'draft'

        if not title or not description or not address or not preferred_date:
            messages.error(request, 'Please fill in all required fields.')
            return render(request, 'jobs/job_form.html', {'categories': CATEGORY_CHOICES})

        lat = request.POST.get('latitude', '')
        lng = request.POST.get('longitude', '')

        job = Job.objects.create(
            customer=request.user,
            title=title,
            description=description,
            category=category,
            address=address,
            latitude=float(lat) if lat else None,
            longitude=float(lng) if lng else None,
            budget=int(budget) if budget.isdigit() else 0,
            hours_needed=int(hours_needed) if hours_needed.isdigit() else 1,
            preferred_date=preferred_date,
            workers_needed=int(workers_needed) if workers_needed.isdigit() else 1,
            status=status,
        )

        photos = request.FILES.getlist('photos')
        for photo in photos:
            if photo.content_type in ALLOWED_TYPES and photo.size <= MAX_SIZE:
                JobPhoto.objects.create(job=job, image=photo)

        if status == 'open':
            messages.success(request, 'Job posted successfully!')
            notify_new_job(job)
        else:
            messages.success(request, 'Job saved as draft.')

        return redirect('job_detail', pk=job.pk)
    return render(request, 'jobs/job_form.html', {'categories': CATEGORY_CHOICES})


@login_required
def job_edit(request, pk):
    job = get_object_or_404(Job, pk=pk, customer=request.user)
    CATEGORY_CHOICES = Job.CATEGORY_CHOICES
    if request.method == 'POST':
        job.title = request.POST.get('title', job.title).strip()
        job.description = request.POST.get('description', job.description).strip()
        job.category = request.POST.get('category', job.category)
        job.address = request.POST.get('address', job.address).strip()
        lat = request.POST.get('latitude', '')
        lng = request.POST.get('longitude', '')
        if lat:
            job.latitude = float(lat)
        if lng:
            job.longitude = float(lng)
        budget = request.POST.get('budget', str(job.budget))
        job.budget = int(budget) if budget.isdigit() else job.budget
        hours = request.POST.get('hours_needed', str(job.hours_needed))
        job.hours_needed = int(hours) if hours.isdigit() else job.hours_needed
        job.preferred_date = request.POST.get('preferred_date', job.preferred_date)
        workers = request.POST.get('workers_needed', str(job.workers_needed))
        job.workers_needed = int(workers) if workers.isdigit() else job.workers_needed
        new_status = request.POST.get('status', job.status)
        if new_status in dict(Job.STATUS_CHOICES):
            job.status = new_status
        job.save()

        photos = request.FILES.getlist('photos')
        for photo in photos:
            if photo.content_type in ALLOWED_TYPES and photo.size <= MAX_SIZE:
                JobPhoto.objects.create(job=job, image=photo)

        messages.success(request, 'Job updated.')
        return redirect('job_detail', pk=job.pk)
    return render(request, 'jobs/job_form.html', {
        'job': job,
        'categories': CATEGORY_CHOICES,
    })


@login_required
def job_delete(request, pk):
    if request.method != 'POST':
        return redirect('my_jobs')
    job = get_object_or_404(Job, pk=pk, customer=request.user)
    job.delete()
    messages.success(request, 'Job deleted.')
    return redirect('my_jobs')


@login_required
def my_jobs(request):
    jobs = Job.objects.filter(customer=request.user).order_by('-created_at')
    return render(request, 'jobs/my_jobs.html', {'jobs': jobs})


@login_required
def job_apply(request, pk):
    from profiles.models import WorkerProfile

    if request.method != 'POST':
        return redirect('job_detail', pk=pk)

    job = get_object_or_404(Job, pk=pk, status='open')
    worker_profile = WorkerProfile.objects.filter(user=request.user).first()

    if not worker_profile:
        messages.error(request, 'You need a worker profile to apply for jobs.')
        return redirect('job_detail', pk=pk)

    if job.customer == request.user:
        messages.error(request, 'You cannot apply to your own job.')
        return redirect('job_detail', pk=pk)

    if JobApplication.objects.filter(job=job, worker=worker_profile).exists():
        messages.error(request, 'You have already applied to this job.')
        return redirect('job_detail', pk=pk)

    message = request.POST.get('message', '').strip()
    application = JobApplication.objects.create(job=job, worker=worker_profile, message=message)
    messages.success(request, f'Application sent to {job.customer.username}!')
    notify_application_received(application)
    return redirect('job_detail', pk=pk)


@login_required
def job_action(request, pk):
    job = get_object_or_404(Job, pk=pk, customer=request.user)
    if request.method != 'POST':
        return redirect('job_detail', pk=pk)

    from django.utils import timezone

    action = request.POST.get('action', '')
    if action == 'publish':
        job.status = 'open'
        job.save()
        messages.success(request, 'Job is now open for applications!')
        notify_new_job(job)
    elif action == 'start':
        job.status = 'in_progress'
        job.started_at = timezone.now()
        job.save()
        messages.success(request, 'Job started! Work is now in progress.')
    elif action == 'complete':
        job.status = 'completed'
        job.save()
        messages.success(request, 'Job marked as completed!')
    elif action == 'cancel':
        job.status = 'cancelled'
        job.save()
        messages.success(request, 'Job cancelled.')

    return redirect('job_detail', pk=pk)


@login_required
def application_action(request, job_pk, app_pk):
    job = get_object_or_404(Job, pk=job_pk, customer=request.user)
    application = get_object_or_404(JobApplication, pk=app_pk, job=job)

    if request.method != 'POST':
        return redirect('job_detail', pk=job.pk)

    action = request.POST.get('action', '')
    if action == 'accept':
        application.status = 'accepted'
        application.save()
        job.status = 'assigned'
        job.save()
        messages.success(request, f'{application.worker.name} has been assigned to this job!')
        notify_application_accepted(application)
    elif action == 'reject':
        application.status = 'rejected'
        application.save()
        messages.success(request, 'Application rejected.')
        notify_application_rejected(application)

    return redirect('job_detail', pk=job.pk)
