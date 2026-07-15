from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render

from profiles.models import WorkerProfile

from .models import SearchQuery


SERVICE_INFO = {
    'plumbing': {
        'title': 'Plumbing Services',
        'description': 'Expert plumbing services for repairs, installations, and maintenance. From leaky faucets to pipe installations, our verified workers handle it all.',
        'icon': '🔧',
        'starting_rate': 'Rs. 800',
    },
    'painting': {
        'title': 'Painting Services',
        'description': 'Professional painting services for homes and offices. Interior, exterior, touch-ups, and complete makeovers by skilled painters.',
        'icon': '🎨',
        'starting_rate': 'Rs. 1,200',
    },
    'electrical work': {
        'title': 'Electrical Services',
        'description': 'Safe and reliable electrical services. Wiring, fixtures, switches, fans, and lighting installation by certified electricians.',
        'icon': '⚡',
        'starting_rate': 'Rs. 900',
    },
    'home cleaning': {
        'title': 'Home Cleaning Services',
        'description': 'Deep cleaning, regular maintenance, and specialized cleaning services. Keep your home spotless with our trusted workers.',
        'icon': '🧹',
        'starting_rate': 'Rs. 600',
    },
    'furniture assembly, mounting': {
        'title': 'Furniture Assembly & Mounting',
        'description': 'Expert assembly of beds, desks, shelves, wardrobes, and mounting of TVs, mirrors, and decor items.',
        'icon': '🔨',
        'starting_rate': 'Rs. 900',
    },
    'gardening & yard work': {
        'title': 'Gardening & Yard Work',
        'description': 'Garden maintenance, lawn care, landscaping, and yard cleanup services. Keep your outdoor spaces beautiful.',
        'icon': '🌿',
        'starting_rate': 'Rs. 500',
    },
    'moving help': {
        'title': 'Moving Help',
        'description': 'Professional moving assistance for loading, unloading, packing, and relocation. Make your move stress-free.',
        'icon': '📦',
        'starting_rate': 'Rs. 1,000',
    },
    'tv mounting & setup': {
        'title': 'TV Mounting & Setup',
        'description': 'Expert TV mounting, wall installation, and home theater setup. Get the perfect viewing experience.',
        'icon': '📺',
        'starting_rate': 'Rs. 1,200',
    },
}

POPULAR_PROJECTS = {
    'furniture-assembly': {
        'title': 'Furniture Assembly',
        'description': 'Get help assembling beds, desks, shelves, wardrobes, and more. Our verified workers have the tools and expertise to build your furniture quickly and correctly.',
        'icon': '🔨',
        'starting_rate': 'Rs. 1,200',
        'skills': ['Furniture Assembly', 'Mounting'],
        'tasks': ['Bed assembly', 'Desk setup', 'Shelf installation', 'Wardrobe building', 'Cabinet assembly', 'Table construction'],
    },
    'mount-art-or-shelves': {
        'title': 'Mount Art or Shelves',
        'description': 'Professional mounting of artwork, shelves, mirrors, curtains, frames, and decor. Get everything hung perfectly on your walls.',
        'icon': '🖼️',
        'starting_rate': 'Rs. 900',
        'skills': ['Mounting', 'Furniture Assembly'],
        'tasks': ['Picture hanging', 'Shelf mounting', 'Mirror installation', 'Curtain rod setup', 'Frame mounting', 'Wall decor'],
    },
    'tv-mounting': {
        'title': 'TV Mounting',
        'description': 'Expert TV mounting and setup services. We handle all TV sizes, wall types, and cable management for a clean installation.',
        'icon': '📺',
        'starting_rate': 'Rs. 1,500',
        'skills': ['TV Mounting', 'Mounting', 'Electrical Work'],
        'tasks': ['TV wall mounting', 'Cable management', 'Soundbar setup', 'Media console assembly', 'Home theater setup', 'Bracket installation'],
    },
    'help-moving': {
        'title': 'Help Moving',
        'description': 'Professional moving assistance for loading, unloading, packing, and relocation. Make your move stress-free with strong, careful workers.',
        'icon': '📦',
        'starting_rate': 'Rs. 1,800',
        'skills': ['Moving Help', 'Furniture Assembly'],
        'tasks': ['Loading trucks', 'Unloading boxes', 'Furniture disassembly', 'Packing services', 'Heavy lifting', 'Relocation help'],
    },
    'home-cleaning': {
        'title': 'Home Cleaning',
        'description': 'Deep cleaning, regular maintenance, and specialized cleaning services. Keep your home spotless with our trusted workers.',
        'icon': '🧹',
        'starting_rate': 'Rs. 1,000',
        'skills': ['Home Cleaning'],
        'tasks': ['Deep cleaning', 'Kitchen cleaning', 'Bathroom sanitizing', 'Floor mopping', 'Window cleaning', 'Regular maintenance'],
    },
    'minor-repairs': {
        'title': 'Minor Repairs',
        'description': 'Small plumbing, electrical, fixture, door, and furniture fixes. Get your home back in shape with quick, affordable repairs.',
        'icon': '🔧',
        'starting_rate': 'Rs. 1,400',
        'skills': ['Plumbing', 'Electrical Work', 'Furniture Assembly'],
        'tasks': ['Leak fixes', 'Switch replacement', 'Door repair', 'Furniture touch-up', 'Fixture installation', 'Small fixes'],
    },
    'heavy-lifting': {
        'title': 'Heavy Lifting',
        'description': 'Strong workers for heavy lifting tasks. Moving furniture, carrying items, and physically demanding jobs made easy.',
        'icon': '💪',
        'starting_rate': 'Rs. 1,600',
        'skills': ['Moving Help', 'Furniture Assembly'],
        'tasks': ['Furniture moving', 'Heavy item carrying', 'Construction cleanup', 'Warehouse help', 'Event setup', 'Bulk transport'],
    },
    'light-installation': {
        'title': 'Light Installation',
        'description': 'Professional lighting installation for homes and offices. Ceiling fans, chandeliers, recessed lights, and more.',
        'icon': '💡',
        'starting_rate': 'Rs. 1,300',
        'skills': ['Electrical Work', 'Mounting'],
        'tasks': ['Ceiling fan install', 'Chandelier mounting', 'Recessed lighting', 'Fixture replacement', 'Outdoor lights', 'Dimmer switches'],
    },
    'yard-cleanup': {
        'title': 'Yard Cleanup',
        'description': 'Garden cleanup, lawn care, landscaping, and yard maintenance. Keep your outdoor spaces clean and beautiful.',
        'icon': '🌿',
        'starting_rate': 'Rs. 1,100',
        'skills': ['Gardening & Yard Work'],
        'tasks': ['Lawn mowing', 'Leaf raking', 'Garden weeding', 'Hedge trimming', 'Yard waste removal', 'Planting'],
    },
    'painting': {
        'title': 'Painting',
        'description': 'Interior painting, touch-ups, doors, trims, and fence painting. Professional painters for a fresh, clean look.',
        'icon': '🎨',
        'starting_rate': 'Rs. 2,000',
        'skills': ['Painting'],
        'tasks': ['Interior painting', 'Touch-ups', 'Door painting', 'Trim work', 'Fence painting', 'Accent walls'],
    },
}


def home(request):
    workers = WorkerProfile.objects.filter(is_available=True).order_by('-created_at')[:8]
    categories = (
        WorkerProfile.objects
        .filter(is_available=True)
        .values('skill')
        .annotate(count=Count('id'))
        .order_by('-count')
    )
    return render(request, 'core/home.html', {
        'workers': workers,
        'categories': categories,
    })


def services(request):
    categories = (
        WorkerProfile.objects
        .filter(is_available=True)
        .values('skill')
        .annotate(count=Count('id'))
        .order_by('-count')
    )
    return render(request, 'core/services.html', {'categories': categories})


def popular_projects(request):
    projects = []
    for slug, info in POPULAR_PROJECTS.items():
        skills_q = Q()
        for skill in info['skills']:
            skills_q |= Q(skill__icontains=skill)
        count = WorkerProfile.objects.filter(skills_q, is_available=True).count()
        projects.append({
            'slug': slug,
            'title': info['title'],
            'icon': info['icon'],
            'starting_rate': info['starting_rate'],
            'count': count,
        })
    return render(request, 'core/popular_projects.html', {'projects': projects})


def project_detail(request, slug):
    project = POPULAR_PROJECTS.get(slug)
    if not project:
        from django.http import Http404
        raise Http404

    skills_q = Q()
    for skill in project['skills']:
        skills_q |= Q(skill__icontains=skill)

    workers = WorkerProfile.objects.filter(
        skills_q, is_available=True
    ).order_by('-rating', '-jobs_count')

    total_workers = workers.count()
    avg_rating = 0
    if total_workers > 0:
        from django.db.models import Avg
        avg_rating = workers.aggregate(avg=Avg('rating'))['avg'] or 0

    other_projects = []
    for s, info in POPULAR_PROJECTS.items():
        if s != slug:
            other_projects.append({'slug': s, 'title': info['title'], 'icon': info['icon']})

    return render(request, 'core/project_detail.html', {
        'slug': slug,
        'project': project,
        'workers': workers,
        'total_workers': total_workers,
        'avg_rating': round(avg_rating, 1),
        'other_projects': other_projects,
    })


def how_it_works(request):
    return render(request, 'core/how_it_works.html')


def service_detail(request, skill):
    service = SERVICE_INFO.get(skill.lower(), {
        'title': skill,
        'description': f'Professional {skill.lower()} services by verified workers.',
        'icon': '🔧',
        'starting_rate': 'Rs. 500',
    })

    workers = WorkerProfile.objects.filter(
        skill__icontains=skill,
        is_available=True,
    ).order_by('-rating', '-jobs_count')

    total_workers = workers.count()
    avg_rating = 0
    if total_workers > 0:
        from django.db.models import Avg
        avg_rating = workers.aggregate(avg=Avg('rating'))['avg'] or 0

    categories = (
        WorkerProfile.objects
        .filter(is_available=True)
        .values('skill')
        .annotate(count=Count('id'))
        .order_by('-count')
    )

    return render(request, 'core/service_detail.html', {
        'skill': skill,
        'service': service,
        'workers': workers,
        'total_workers': total_workers,
        'avg_rating': round(avg_rating, 1),
        'categories': categories,
    })


def search(request):
    query = request.GET.get('q', '').strip()
    workers = []
    results_count = 0

    if query:
        workers = WorkerProfile.objects.filter(
            Q(skill__icontains=query) |
            Q(name__icontains=query) |
            Q(bio__icontains=query) |
            Q(location__icontains=query),
            is_available=True,
        ).order_by('-rating', '-jobs_count')

        results_count = workers.count()

        user = request.user if request.user.is_authenticated else None
        SearchQuery.objects.create(
            keyword=query,
            user=user,
            results_count=results_count,
        )

    return render(request, 'core/search.html', {
        'query': query,
        'workers': workers,
        'results_count': results_count,
    })


def search_suggestions(request):
    q = request.GET.get('q', '').strip()
    if len(q) < 2:
        return JsonResponse({'suggestions': []})

    skills = (
        WorkerProfile.objects
        .filter(skill__icontains=q, is_available=True)
        .values_list('skill', flat=True)
        .distinct()[:5]
    )

    names = (
        WorkerProfile.objects
        .filter(name__icontains=q, is_available=True)
        .values_list('name', flat=True)
        .distinct()[:5]
    )

    locations = (
        WorkerProfile.objects
        .filter(location__icontains=q, is_available=True)
        .exclude(location='')
        .values_list('location', flat=True)
        .distinct()[:5]
    )

    popular = (
        SearchQuery.objects
        .filter(keyword__icontains=q)
        .values('keyword')
        .annotate(count=Count('id'))
        .order_by('-count')[:5]
        .values_list('keyword', flat=True)
    )

    suggestions = []
    for skill in skills:
        suggestions.append({'text': skill, 'type': 'skill'})
    for name in names:
        suggestions.append({'text': name, 'type': 'worker'})
    for loc in locations:
        suggestions.append({'text': loc, 'type': 'location'})
    for kw in popular:
        suggestions.append({'text': kw, 'type': 'popular'})

    seen = set()
    unique = []
    for s in suggestions:
        key = s['text'].lower()
        if key not in seen:
            seen.add(key)
            unique.append(s)

    return JsonResponse({'suggestions': unique[:10]})
