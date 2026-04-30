from datetime import timedelta

from django.db.models import ExpressionWrapper, F, FloatField, Prefetch, Value
from django.db.models.functions import ACos, Cos, Radians, Sin
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import IsAuthenticated

from .filters import RideFilter
from .models import Ride, Ride_Event
from .serializers import RideSerializer
from nemt_ride.permissions import IsAdmin


class RideViewSet(viewsets.ModelViewSet):
    serializer_class = RideSerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = RideFilter
    ordering_fields = ['pickup_time', 'distance_to_pickup']
    ordering = ['-pickup_time']

    def _todays_events_prefetch(self):
        """Prefetch only ride events from the last 24 hours — never loads full history."""
        since = timezone.now() - timedelta(hours=24)
        return Prefetch(
            'ride_events',
            queryset=Ride_Event.objects.filter(created_at__gte=since),
            to_attr='todays_ride_events',
        )

    def _distance_annotation(self, lat: float, lon: float):
        """
        Haversine distance (km) from a GPS point to each ride's pickup location.
        Computed entirely in the DB — efficient for large tables and compatible
        with ORDER BY and pagination.
        """
        return ExpressionWrapper(
            ACos(
                Sin(Radians(Value(lat))) * Sin(Radians(F('pickup_latitude'))) +
                Cos(Radians(Value(lat))) * Cos(Radians(F('pickup_latitude'))) *
                Cos(Radians(F('pickup_longitude')) - Radians(Value(lon)))
            ) * Value(6371.0),
            output_field=FloatField(),
        )

    def get_queryset(self):
        # Query 1: Ride + status + rider + driver via select_related
        # Query 2: filtered RideEvents via prefetch_related (Prefetch to_attr)
        # Query 3 (pagination only): COUNT(*)
        qs = (
            Ride.objects
            .select_related('status', 'id_rider', 'id_driver')
            .prefetch_related(self._todays_events_prefetch())
        )

        lat = self.request.query_params.get('lat')
        lon = self.request.query_params.get('lon')
        if lat is not None and lon is not None:
            try:
                qs = qs.annotate(
                    distance_to_pickup=self._distance_annotation(float(lat), float(lon))
                )
            except (ValueError, TypeError):
                pass

        return qs
