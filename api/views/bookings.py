from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from profiles.models import Booking
from profiles.serializers import BookingSerializer


class BookingListCreateView(generics.ListCreateAPIView):
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        email = user.email
        # Customer sees their bookings, worker sees bookings for their profile
        qs = Booking.objects.filter(customer_email=email)
        if hasattr(user, 'worker_profile'):
            qs = qs | Booking.objects.filter(worker=user.worker_profile)
        return qs.select_related('worker').order_by('-created_at')

    def perform_create(self, serializer):
        user = self.request.user
        data = serializer.validated_data
        # Auto-fill customer info from logged-in user
        data['customer_name'] = data.get('customer_name', user.profile.full_name or user.username)
        data['customer_email'] = user.email
        serializer.save(**data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def respond_booking(request, pk):
    booking = Booking.objects.filter(pk=pk).first()
    if not booking:
        return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

    user = request.user
    if not hasattr(user, 'worker_profile') or booking.worker != user.worker_profile:
        return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)

    action = request.data.get('action')
    if action not in ['accept', 'reject']:
        return Response({'error': 'Action must be accept or reject'}, status=status.HTTP_400_BAD_REQUEST)

    booking.status = 'accepted' if action == 'accept' else 'rejected'
    booking.response_message = request.data.get('message', '')
    booking.save()
    return Response({'message': f'Booking {booking.status}'})
