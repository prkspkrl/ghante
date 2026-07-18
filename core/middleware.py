import time
from collections import defaultdict
from django.conf import settings
from django.http import JsonResponse


class RateLimitMiddleware:
    """Simple in-memory rate limiter per IP address."""

    def __init__(self, get_response):
        self.get_response = get_response
        self.requests = defaultdict(list)

    def __call__(self, request):
        ip = self._get_ip(request)
        now = time.time()
        window = getattr(settings, 'RATE_LIMIT_WINDOW', 60)
        max_requests = getattr(settings, 'RATE_LIMIT_REQUESTS', 60)

        self.requests[ip] = [t for t in self.requests[ip] if now - t < window]

        if len(self.requests[ip]) >= max_requests:
            return JsonResponse(
                {'error': 'Too many requests. Please try again later.'},
                status=429,
            )

        self.requests[ip].append(now)
        return self.get_response(request)

    def _get_ip(self, request):
        x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded:
            return x_forwarded.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '0.0.0.0')
