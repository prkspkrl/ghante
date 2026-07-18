from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Count, Sum, Q, Avg
from django.utils import timezone
from datetime import timedelta

from .models import Category


def admin_check(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)


@login_required
@user_passes_test(admin_check)
def admin_dashboard(request):
    from profiles.models import WorkerProfile
    from jobs.models import Job, JobApplication
    from reviews.models import Review
    from payments.models import Payment
    from verification.models import VerificationRequest
    from notifications.models import Notification

    now = timezone.now()
    thirty_days_ago = now - timedelta(days=30)

    stats = {
        'total_users': User.objects.count(),
        'total_workers': WorkerProfile.objects.count(),
        'total_jobs': Job.objects.count(),
        'open_jobs': Job.objects.filter(status='open').count(),
        'completed_jobs': Job.objects.filter(status='completed').count(),
        'total_reviews': Review.objects.count(),
        'pending_kyc': VerificationRequest.objects.filter(status='pending').count(),
        'total_payments': Payment.objects.count(),
        'total_revenue': Payment.objects.filter(status='paid').aggregate(t=Sum('amount'))['t'] or 0,
        'new_users_30d': User.objects.filter(date_joined__gte=thirty_days_ago).count(),
        'new_jobs_30d': Job.objects.filter(created_at__gte=thirty_days_ago).count(),
        'pending_applications': JobApplication.objects.filter(status='pending').count(),
        'unread_notifications': Notification.objects.filter(is_read=False).count(),
    }

    recent_jobs = Job.objects.order_by('-created_at')[:5]
    recent_users = User.objects.order_by('-date_joined')[:5]
    recent_reviews = Review.objects.select_related('reviewer', 'worker').order_by('-created_at')[:5]
    jobs_by_status = list(Job.objects.values('status').annotate(count=Count('id')))
    jobs_by_category = list(Job.objects.values('category').annotate(count=Count('id')).order_by('-count')[:6])

    return render(request, 'admin_panel/dashboard.html', {
        'stats': stats,
        'recent_jobs': recent_jobs,
        'recent_users': recent_users,
        'recent_reviews': recent_reviews,
        'jobs_by_status': jobs_by_status,
        'jobs_by_category': jobs_by_category,
    })


@login_required
@user_passes_test(admin_check)
def admin_users(request):
    q = request.GET.get('q', '').strip()
    role = request.GET.get('role', '')
    users = User.objects.select_related('profile').order_by('-date_joined')
    if q:
        users = users.filter(
            Q(username__icontains=q) | Q(email__icontains=q) |
            Q(first_name__icontains=q) | Q(last_name__icontains=q)
        )
    if role:
        users = users.filter(profile__role=role)
    return render(request, 'admin_panel/users.html', {
        'users': users, 'query': q, 'selected_role': role,
    })


@login_required
@user_passes_test(admin_check)
def admin_user_detail(request, pk):
    from profiles.models import WorkerProfile, Booking
    from jobs.models import Job, JobApplication
    from reviews.models import Review
    user_obj = get_object_or_404(User, pk=pk)
    profile = getattr(user_obj, 'profile', None)
    worker_profile = WorkerProfile.objects.filter(user=user_obj).first()
    jobs_posted = Job.objects.filter(customer=user_obj).order_by('-created_at')[:10]
    applications = JobApplication.objects.filter(worker=worker_profile).order_by('-created_at')[:10] if worker_profile else []
    reviews = Review.objects.filter(reviewer=user_obj).order_by('-created_at')[:10]
    bookings = Booking.objects.filter(worker=worker_profile).order_by('-created_at')[:10] if worker_profile else []
    if request.method == 'POST':
        action = request.POST.get('action', '')
        if action == 'toggle_active':
            user_obj.is_active = not user_obj.is_active
            user_obj.save(update_fields=['is_active'])
            messages.success(request, f'User {user_obj.username} {"activated" if user_obj.is_active else "deactivated"}.')
        elif action == 'toggle_staff':
            user_obj.is_staff = not user_obj.is_staff
            user_obj.save(update_fields=['is_staff'])
            messages.success(request, f'Staff status {"granted" if user_obj.is_staff else "revoked"}.')
        elif action == 'verify' and profile:
            profile.is_verified = not profile.is_verified
            profile.save(update_fields=['is_verified'])
            messages.success(request, f'Verification {"approved" if profile.is_verified else "revoked"}.')
        return redirect('admin_user_detail', pk=pk)
    return render(request, 'admin_panel/user_detail.html', {
        'user_obj': user_obj, 'profile': profile, 'worker_profile': worker_profile,
        'jobs_posted': jobs_posted, 'applications': applications,
        'reviews': reviews, 'bookings': bookings,
    })


@login_required
@user_passes_test(admin_check)
def admin_jobs(request):
    from jobs.models import Job
    q = request.GET.get('q', '').strip()
    status = request.GET.get('status', '')
    category = request.GET.get('category', '')
    jobs = Job.objects.select_related('customer').order_by('-created_at')
    if q:
        jobs = jobs.filter(
            Q(title__icontains=q) | Q(description__icontains=q) |
            Q(address__icontains=q) | Q(customer__username__icontains=q)
        )
    if status:
        jobs = jobs.filter(status=status)
    if category:
        jobs = jobs.filter(category=category)
    return render(request, 'admin_panel/jobs.html', {
        'jobs': jobs, 'query': q, 'selected_status': status,
        'selected_category': category, 'status_choices': Job.STATUS_CHOICES,
        'category_choices': Job.CATEGORY_CHOICES,
    })


@login_required
@user_passes_test(admin_check)
def admin_job_detail(request, pk):
    from jobs.models import Job, JobApplication, JobPhoto
    job = get_object_or_404(Job, pk=pk)
    applications = JobApplication.objects.select_related('worker').filter(job=job)
    photos = JobPhoto.objects.filter(job=job)
    if request.method == 'POST':
        action = request.POST.get('action', '')
        if action == 'update_status':
            new_status = request.POST.get('new_status', '')
            if new_status in dict(Job.STATUS_CHOICES):
                job.status = new_status
                job.save(update_fields=['status'])
                messages.success(request, f'Job status updated to {new_status}.')
        elif action == 'delete':
            job.delete()
            messages.success(request, 'Job deleted.')
            return redirect('admin_jobs')
        return redirect('admin_job_detail', pk=pk)
    return render(request, 'admin_panel/job_detail.html', {
        'job': job, 'applications': applications, 'photos': photos,
    })


@login_required
@user_passes_test(admin_check)
def admin_categories(request):
    from jobs.models import Job
    categories = Category.objects.order_by('sort_order', 'name')
    from jobs.models import Job
    cat_job_counts = dict(Job.objects.values_list('category').annotate(count=Count('id')).values_list('category', 'count'))
    for cat in categories:
        cat.job_count = cat_job_counts.get(cat.slug, 0)
    if request.method == 'POST':
        action = request.POST.get('action', '')
        if action == 'create':
            name = request.POST.get('name', '').strip()
            slug = request.POST.get('slug', '').strip()
            description = request.POST.get('description', '').strip()
            icon = request.POST.get('icon', '').strip()
            if name and slug:
                Category.objects.create(name=name, slug=slug, description=description, icon=icon)
                messages.success(request, f'Category "{name}" created.')
            else:
                messages.error(request, 'Name and slug are required.')
        elif action == 'toggle':
            cat = Category.objects.filter(pk=request.POST.get('category_id', '')).first()
            if cat:
                cat.is_active = not cat.is_active
                cat.save(update_fields=['is_active'])
                messages.success(request, f'Category "{cat.name}" {"activated" if cat.is_active else "deactivated"}.')
        elif action == 'delete':
            cat = Category.objects.filter(pk=request.POST.get('category_id', '')).first()
            if cat:
                cat.delete()
                messages.success(request, f'Category deleted.')
        elif action == 'update':
            cat = Category.objects.filter(pk=request.POST.get('category_id', '')).first()
            if cat:
                cat.name = request.POST.get('name', cat.name).strip()
                cat.slug = request.POST.get('slug', cat.slug).strip()
                cat.description = request.POST.get('description', cat.description).strip()
                cat.icon = request.POST.get('icon', cat.icon).strip()
                cat.sort_order = int(request.POST.get('sort_order', cat.sort_order))
                cat.save()
                messages.success(request, f'Category "{cat.name}" updated.')
        return redirect('admin_categories')
    return render(request, 'admin_panel/categories.html', {
        'categories': categories, 'cat_job_counts': cat_job_counts,
    })


@login_required
@user_passes_test(admin_check)
def admin_kyc(request):
    from verification.models import VerificationRequest
    status_filter = request.GET.get('status', '')
    reqs = VerificationRequest.objects.order_by('-submitted_at')
    if status_filter:
        reqs = reqs.filter(status=status_filter)
    if request.method == 'POST':
        action = request.POST.get('action', '')
        req = VerificationRequest.objects.filter(pk=request.POST.get('request_id', '')).first()
        if req:
            if action == 'approve':
                req.status = 'approved'
                req.save(update_fields=['status'])
                messages.success(request, f'Approved: {req.applicant_name}')
            elif action == 'reject':
                req.status = 'rejected'
                req.save(update_fields=['status'])
                messages.success(request, f'Rejected: {req.applicant_name}')
        return redirect('admin_kyc')
    return render(request, 'admin_panel/kyc.html', {
        'requests': reqs, 'selected_status': status_filter,
    })


@login_required
@user_passes_test(admin_check)
def admin_reviews(request):
    from reviews.models import Review
    q = request.GET.get('q', '').strip()
    review_type = request.GET.get('type', '')
    rating = request.GET.get('rating', '')
    reviews = Review.objects.select_related('reviewer', 'worker', 'job').order_by('-created_at')
    if q:
        reviews = reviews.filter(
            Q(reviewer__username__icontains=q) | Q(worker__name__icontains=q) | Q(comment__icontains=q)
        )
    if review_type:
        reviews = reviews.filter(review_type=review_type)
    if rating:
        reviews = reviews.filter(rating=rating)
    if request.method == 'POST' and request.POST.get('action') == 'delete':
        Review.objects.filter(pk=request.POST.get('review_id', '')).delete()
        messages.success(request, 'Review deleted.')
        return redirect('admin_reviews')
    return render(request, 'admin_panel/reviews.html', {
        'reviews': reviews, 'query': q, 'selected_type': review_type, 'selected_rating': rating,
    })


@login_required
@user_passes_test(admin_check)
def admin_payments(request):
    from payments.models import Payment
    q = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '')
    payments = Payment.objects.order_by('-created_at')
    if q:
        payments = payments.filter(Q(payer_name__icontains=q) | Q(reference__icontains=q))
    if status_filter:
        payments = payments.filter(status=status_filter)
    if request.method == 'POST':
        action = request.POST.get('action', '')
        pay = Payment.objects.filter(pk=request.POST.get('payment_id', '')).first()
        if pay:
            if action == 'update_status':
                new_status = request.POST.get('new_status', '')
                if new_status in dict(Payment.STATUS_CHOICES):
                    pay.status = new_status
                    pay.save(update_fields=['status'])
                    messages.success(request, f'Payment updated to {new_status}.')
            elif action == 'delete':
                pay.delete()
                messages.success(request, 'Payment deleted.')
        return redirect('admin_payments')
    return render(request, 'admin_panel/payments.html', {
        'payments': payments, 'query': q, 'selected_status': status_filter,
    })


@login_required
@user_passes_test(admin_check)
def admin_reports(request):
    from profiles.models import WorkerProfile
    from jobs.models import Job, JobApplication
    from reviews.models import Review
    from payments.models import Payment
    from verification.models import VerificationRequest

    now = timezone.now()
    periods = {
        '7d': now - timedelta(days=7),
        '30d': now - timedelta(days=30),
        '90d': now - timedelta(days=90),
        '365d': now - timedelta(days=365),
    }
    period = request.GET.get('period', '30d')
    since = periods.get(period, periods['30d'])

    report = {
        'new_users': User.objects.filter(date_joined__gte=since).count(),
        'new_workers': WorkerProfile.objects.filter(created_at__gte=since).count(),
        'new_jobs': Job.objects.filter(created_at__gte=since).count(),
        'completed_jobs': Job.objects.filter(status='completed', updated_at__gte=since).count(),
        'new_applications': JobApplication.objects.filter(created_at__gte=since).count(),
        'accepted_applications': JobApplication.objects.filter(status='accepted', created_at__gte=since).count(),
        'new_reviews': Review.objects.filter(created_at__gte=since).count(),
        'avg_rating': Review.objects.filter(created_at__gte=since).aggregate(a=Avg('rating'))['a'] or 0,
        'new_payments': Payment.objects.filter(created_at__gte=since).count(),
        'revenue': Payment.objects.filter(status='paid', created_at__gte=since).aggregate(t=Sum('amount'))['t'] or 0,
        'pending_kyc': VerificationRequest.objects.filter(status='pending').count(),
        'approved_kyc': VerificationRequest.objects.filter(status='approved', submitted_at__gte=since).count(),
    }

    top_categories = list(Job.objects.filter(created_at__gte=since).values('category').annotate(count=Count('id')).order_by('-count')[:6])
    top_workers = list(WorkerProfile.objects.annotate(review_count=Count('reviews')).order_by('-review_count')[:5])
    monthly_jobs = list(
        Job.objects.filter(created_at__gte=since)
        .extra(select={'month': "strftime('%%Y-%%m', created_at)"})
        .values('month').annotate(count=Count('id')).order_by('month')
    )

    return render(request, 'admin_panel/reports.html', {
        'report': report, 'selected_period': period, 'periods': periods,
        'top_categories': top_categories, 'top_workers': top_workers,
        'monthly_jobs': monthly_jobs,
    })
