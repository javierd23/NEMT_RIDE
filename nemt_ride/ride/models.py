from django.db import models
from django.conf import settings 


class RideStatus(models.Model):
    """I added the status of the ride as a separate model since it is 
    more efficient and we can easily add more statuses in the future if needed"""
    #id 1 requested
    #id 2 en-route
    #id 3 picked-up
    #id 4 started
    #id 5 dropped-off
    #id 6 cancelled 
    status = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.status


class Ride(models.Model):
    id_ride = models.AutoField(primary_key=True)

    status = models.ForeignKey(RideStatus, on_delete=models.SET_DEFAULT, default=1,
                               related_name='rides_status')
    
    id_rider = models.ForeignKey(settings.AUTH_USER_MODEL, 
                                 on_delete=models.CASCADE, related_name='rides_as_rider')
    
    id_driver = models.ForeignKey(settings.AUTH_USER_MODEL, 
                                 on_delete=models.CASCADE, related_name='rides_as_driver', 
                                 null=True, blank=True) # in case there is no driver assigned yet.
    
    pickup_latitude = models.FloatField(null=True, blank=True)
    pickup_longitude = models.FloatField(null=True, blank=True)
    dropoff_latitude = models.FloatField(null=True, blank=True)
    dropoff_longitude = models.FloatField(null=True, blank=True)

    updated_at = models.DateTimeField(auto_now=True)

    pickup_time = models.DateTimeField()

    def __str__(self):
        return f"Ride from ({self.pickup_latitude}, {self.pickup_longitude}) to ({self.dropoff_latitude}, {self.dropoff_longitude}) on {self.pickup_time}"

    class Meta:
        indexes = [
            models.Index(fields=['pickup_time']),
            models.Index(fields=['status']),
            models.Index(fields=['id_rider']),
        ]

class Ride_Event(models.Model):
    id_ride_event = models.AutoField(primary_key=True)
    id_ride = models.ForeignKey(Ride, on_delete=models.CASCADE, related_name='ride_events')

    description = models.CharField(max_length=300)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Event {self.id_ride_event} on Ride {self.id_ride_id}: {self.description[:50]}"