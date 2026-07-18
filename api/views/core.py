from django.db.models import Count, Q
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from profiles.models import WorkerProfile
from core.models import SearchQuery
from jobs.models import Job

WORKER_Q = Q(user__isnull=True) | Q(user__profile__is_worker=True)

SERVICE_INFO = {
    'plumbing': {'title': 'Plumbing Services', 'icon': '🔧', 'starting_rate': 'Rs. 800'},
    'painting': {'title': 'Painting Services', 'icon': '🎨', 'starting_rate': 'Rs. 1,200'},
    'electrical work': {'title': 'Electrical Services', 'icon': '⚡', 'starting_rate': 'Rs. 900'},
    'home cleaning': {'title': 'Home Cleaning Services', 'icon': '🧹', 'starting_rate': 'Rs. 600'},
    'furniture assembly, mounting': {'title': 'Furniture Assembly & Mounting', 'icon': '🔨', 'starting_rate': 'Rs. 900'},
    'gardening & yard work': {'title': 'Gardening & Yard Work', 'icon': '🌿', 'starting_rate': 'Rs. 500'},
    'moving help': {'title': 'Moving Help', 'icon': '📦', 'starting_rate': 'Rs. 1,000'},
    'tv mounting & setup': {'title': 'TV Mounting & Setup', 'icon': '📺', 'starting_rate': 'Rs. 1,200'},
}

POPULAR_PROJECTS = {
    'furniture-assembly': {'title': 'Furniture Assembly', 'icon': '🔨', 'starting_rate': 'Rs. 1,200', 'skills': ['Furniture Assembly', 'Mounting']},
    'mount-art-or-shelves': {'title': 'Mount Art or Shelves', 'icon': '🖼️', 'starting_rate': 'Rs. 900', 'skills': ['Mounting', 'Furniture Assembly']},
    'tv-mounting': {'title': 'TV Mounting', 'icon': '📺', 'starting_rate': 'Rs. 1,500', 'skills': ['TV Mounting', 'Mounting', 'Electrical Work']},
    'help-moving': {'title': 'Help Moving', 'icon': '📦', 'starting_rate': 'Rs. 1,800', 'skills': ['Moving Help', 'Furniture Assembly']},
    'home-cleaning': {'title': 'Home Cleaning', 'icon': '🧹', 'starting_rate': 'Rs. 1,000', 'skills': ['Home Cleaning']},
    'minor-repairs': {'title': 'Minor Repairs', 'icon': '🔧', 'starting_rate': 'Rs. 1,400', 'skills': ['Plumbing', 'Electrical Work', 'Furniture Assembly']},
    'heavy-lifting': {'title': 'Heavy Lifting', 'icon': '💪', 'starting_rate': 'Rs. 1,600', 'skills': ['Moving Help', 'Furniture Assembly']},
    'light-installation': {'title': 'Light Installation', 'icon': '💡', 'starting_rate': 'Rs. 1,300', 'skills': ['Electrical Work', 'Mounting']},
    'yard-cleanup': {'title': 'Yard Cleanup', 'icon': '🌿', 'starting_rate': 'Rs. 1,100', 'skills': ['Gardening & Yard Work']},
    'painting': {'title': 'Painting', 'icon': '🎨', 'starting_rate': 'Rs. 2,000', 'skills': ['Painting']},
}


@api_view(['GET'])
@permission_classes([AllowAny])
def search_suggestions(request):
    q = request.GET.get('q', '').strip()
    if len(q) < 2:
        return Response({'suggestions': []})

    skills = WorkerProfile.objects.filter(
        WORKER_Q, skill__icontains=q, is_available=True,
    ).values_list('skill', flat=True).distinct()[:5]

    names = WorkerProfile.objects.filter(
        WORKER_Q, name__icontains=q, is_available=True,
    ).values_list('name', flat=True).distinct()[:5]

    locations = WorkerProfile.objects.filter(
        WORKER_Q, location__icontains=q, is_available=True,
    ).exclude(location='').values_list('location', flat=True).distinct()[:5]

    popular = SearchQuery.objects.filter(
        keyword__icontains=q,
    ).values('keyword').annotate(count=Count('id')).order_by('-count')[:5].values_list('keyword', flat=True)

    suggestions = []
    for s in skills:
        suggestions.append({'text': s, 'type': 'skill'})
    for n in names:
        suggestions.append({'text': n, 'type': 'worker'})
    for l in locations:
        suggestions.append({'text': l, 'type': 'location'})
    for p in popular:
        suggestions.append({'text': p, 'type': 'popular'})

    seen = set()
    unique = []
    for s in suggestions:
        key = s['text'].lower()
        if key not in seen:
            seen.add(key)
            unique.append(s)

    return Response({'suggestions': unique[:10]})


@api_view(['GET'])
@permission_classes([AllowAny])
def global_search(request):
    q = request.GET.get('q', '').strip()
    if not q:
        return Response({'workers': [], 'jobs': [], 'count': 0})

    workers = WorkerProfile.objects.filter(
        WORKER_Q,
        Q(skill__icontains=q) | Q(name__icontains=q) |
        Q(bio__icontains=q) | Q(location__icontains=q),
        is_available=True,
    ).order_by('-rating', '-jobs_count')

    jobs = Job.objects.filter(
        Q(status='open') &
        (Q(title__icontains=q) | Q(description__icontains=q) | Q(category__icontains=q))
    ).order_by('-created_at')

    # Log search
    user = request.user if request.user.is_authenticated else None
    SearchQuery.objects.create(keyword=q, user=user, results_count=workers.count())

    from profiles.serializers import WorkerProfileListSerializer
    from jobs.serializers import JobListSerializer

    return Response({
        'workers': WorkerProfileListSerializer(workers[:20], many=True, context={'request': request}).data,
        'jobs': JobListSerializer(jobs[:20], many=True, context={'request': request}).data,
        'count': workers.count() + jobs.count(),
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def service_categories(request):
    categories = WorkerProfile.objects.filter(
        WORKER_Q, is_available=True,
    ).values('skill').annotate(count=Count('id')).order_by('-count')
    return Response(list(categories))


@api_view(['GET'])
@permission_classes([AllowAny])
def service_detail(request, skill):
    info = SERVICE_INFO.get(skill.lower(), {
        'title': skill,
        'icon': '🔧',
        'starting_rate': 'Rs. 500',
    })
    workers = WorkerProfile.objects.filter(
        WORKER_Q, skill__icontains=skill, is_available=True,
    ).order_by('-rating', '-jobs_count')

    from django.db.models import Avg
    total = workers.count()
    avg_rating = workers.aggregate(avg=Avg('rating'))['avg'] or 0 if total > 0 else 0

    return Response({
        'skill': skill,
        'service': info,
        'total_workers': total,
        'avg_rating': round(avg_rating, 1),
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def popular_projects(request):
    projects = []
    for slug, info in POPULAR_PROJECTS.items():
        skills_q = Q()
        for skill in info['skills']:
            skills_q |= Q(skill__icontains=skill)
        count = WorkerProfile.objects.filter(WORKER_Q, skills_q, is_available=True).count()
        projects.append({
            'slug': slug,
            'title': info['title'],
            'icon': info['icon'],
            'starting_rate': info['starting_rate'],
            'count': count,
        })
    return Response(projects)


@api_view(['GET'])
@permission_classes([AllowAny])
def project_detail(request, slug):
    project = POPULAR_PROJECTS.get(slug)
    if not project:
        return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

    skills_q = Q()
    for skill in project['skills']:
        skills_q |= Q(skill__icontains=skill)

    workers = WorkerProfile.objects.filter(
        WORKER_Q, skills_q, is_available=True,
    ).order_by('-rating', '-jobs_count')

    total = workers.count()
    from django.db.models import Avg
    avg_rating = workers.aggregate(avg=Avg('rating'))['avg'] or 0 if total > 0 else 0

    from profiles.serializers import WorkerProfileListSerializer

    return Response({
        'slug': slug,
        'project': project,
        'workers': WorkerProfileListSerializer(workers[:20], many=True, context={'request': request}).data,
        'total_workers': total,
        'avg_rating': round(avg_rating, 1),
    })
