from rest_framework import serializers
from .models import Ride, Ride_Event


class RideEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ride_Event
        fields = ['id_ride_event', 'description', 'created_at']

class RideSerializer(serializers.ModelSerializer):
    status = serializers.StringRelatedField()

    # Populated via Prefetch(to_attr='todays_ride_events') — never fetches full event list
    todays_ride_events = RideEventSerializer(many=True, read_only=True)
    
    # Only present when lat/lon query params are provided
    distance_to_pickup = serializers.SerializerMethodField()

    class Meta:
        model = Ride
        fields = [
            'id_ride', 'status', 'id_rider', 'id_driver',
            'pickup_latitude', 'pickup_longitude',
            'dropoff_latitude', 'dropoff_longitude',
            'pickup_time', 'todays_ride_events', 'distance_to_pickup',
        ]

    # even though I used serializer method field, the view is the one that decides
    # whether to annotate  and how to compute the distance (the business logic), so this just
    # returns the value if it is present, otherwise None.
    def get_distance_to_pickup(self, obj):
        return getattr(obj, 'distance_to_pickup', None)
