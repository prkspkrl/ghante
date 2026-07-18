from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from profiles.models import Favorite, WorkerProfile
from profiles.serializers import FavoriteSerializer


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def favorite_list(request):
    favorites = Favorite.objects.filter(user=request.user).select_related('worker', 'worker__user').order_by('-created_at')
    serializer = FavoriteSerializer(favorites, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def toggle_favorite(request, worker_id):
    worker = WorkerProfile.objects.filter(pk=worker_id).first()
    if not worker:
        return Response({'error': 'Worker not found'}, status=status.HTTP_404_NOT_FOUND)

    fav, created = Favorite.objects.get_or_create(user=request.user, worker=worker)
    if not created:
        fav.delete()
        return Response({'favorited': False})
    return Response({'favorited': True}, status=status.HTTP_201_CREATED)
