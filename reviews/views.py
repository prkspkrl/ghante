from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .models import Review
from notifications.services import notify_review_created


@login_required
def leave_review_worker(request, worker_pk):
    """Customer reviews a worker after a completed job."""
    from profiles.models import WorkerProfile
    worker = get_object_or_404(WorkerProfile, pk=worker_pk)

    if request.method != 'POST':
        return redirect('worker_detail', pk=worker.pk)

    from jobs.models import Job, JobApplication

    job_id = request.POST.get('job_id', '')
    rating = request.POST.get('rating', '5')
    comment = request.POST.get('comment', '').strip()

    job = None
    if job_id:
        job = get_object_or_404(Job, pk=job_id, customer=request.user, status__in=['assigned', 'in_progress', 'completed'])

    if Review.objects.filter(
        reviewer=request.user, worker=worker, review_type='customer_to_worker',
        job=job
    ).exists():
        messages.error(request, 'You have already reviewed this worker for this job.')
        return redirect('worker_detail', pk=worker.pk)

    try:
        rating_val = int(rating)
    except (ValueError, TypeError):
        rating_val = 5
    rating_val = max(1, min(5, rating_val))

    Review.objects.create(
        reviewer=request.user,
        worker=worker,
        job=job,
        review_type='customer_to_worker',
        rating=rating_val,
        comment=comment[:2000],
    )

    _update_worker_rating(worker)
    notify_review_created(Review.objects.filter(reviewer=request.user, worker=worker, job=job, review_type='customer_to_worker').first())
    messages.success(request, f'Review for {worker.name} submitted!')
    return redirect('worker_detail', pk=worker.pk)


@login_required
def leave_review_customer(request, job_pk):
    """Worker reviews a customer after a completed job."""
    from jobs.models import Job, JobApplication
    from profiles.models import WorkerProfile

    job = get_object_or_404(Job, pk=job_pk, status='completed')
    worker_profile = WorkerProfile.objects.filter(user=request.user).first()

    if not worker_profile:
        messages.error(request, 'You need a worker profile to leave reviews.')
        return redirect('home')

    if not JobApplication.objects.filter(
        job=job, worker=worker_profile, status='accepted'
    ).exists():
        messages.error(request, 'You were not assigned to this job.')
        return redirect('job_detail', pk=job.pk)

    if Review.objects.filter(
        reviewer=request.user, job=job, review_type='worker_to_customer'
    ).exists():
        messages.error(request, 'You have already reviewed this customer.')
        return redirect('job_detail', pk=job.pk)

    if request.method == 'POST':
        rating = request.POST.get('rating', '5')
        comment = request.POST.get('comment', '').strip()

        try:
            rating_val = int(rating)
        except (ValueError, TypeError):
            rating_val = 5
        rating_val = max(1, min(5, rating_val))

        Review.objects.create(
            reviewer=request.user,
            worker=worker_profile,
            job=job,
            review_type='worker_to_customer',
            rating=rating_val,
            comment=comment[:2000],
        )
        notify_review_created(Review.objects.filter(reviewer=request.user, worker=worker_profile, job=job, review_type='worker_to_customer').first())
        messages.success(request, 'Review submitted!')
        return redirect('job_detail', pk=job.pk)

    return render(request, 'reviews/leave_review.html', {
        'job': job,
        'review_type': 'worker_to_customer',
    })


def worker_reviews(request, worker_pk):
    """View all reviews for a worker."""
    from profiles.models import WorkerProfile
    worker = get_object_or_404(WorkerProfile, pk=worker_pk)
    reviews = Review.objects.filter(
        worker=worker, review_type='customer_to_worker'
    ).select_related('reviewer', 'job')
    return render(request, 'reviews/worker_reviews.html', {
        'worker': worker,
        'reviews': reviews,
    })


def _update_worker_rating(worker):
    from django.db.models import Avg
    avg = Review.objects.filter(
        worker=worker, review_type='customer_to_worker'
    ).aggregate(avg=Avg('rating'))['avg']
    if avg:
        worker.rating = round(avg, 1)
        worker.save(update_fields=['rating'])
