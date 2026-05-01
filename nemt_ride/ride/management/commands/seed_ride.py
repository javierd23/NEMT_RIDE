from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from ride.models import Ride, Ride_Event, RideStatus
from user_auth.models import User


class Command(BaseCommand):
    help = 'Seed rides, covering all statuses, GPS coords, and ride events for view testing'

    def handle(self, *args, **kwargs):
        # --- Require users and statuses to exist ---
        try:
            rider1  = User.objects.get(email='rider1@nemt.com')
            rider2  = User.objects.get(email='rider2@nemt.com')
            rider3  = User.objects.get(email='rider3@nemt.com')
            driver1 = User.objects.get(email='driver1@nemt.com')
            driver2 = User.objects.get(email='driver2@nemt.com')
            driver3 = User.objects.get(email='driver3@nemt.com')
        except User.DoesNotExist as e:
            self.stdout.write(self.style.ERROR(f'User missing: {e}. Run seed_user first.'))
            return

        try:
            st_requested  = RideStatus.objects.get(status='requested')
            st_enroute    = RideStatus.objects.get(status='en-route')
            st_pickedup   = RideStatus.objects.get(status='picked-up')
            st_started    = RideStatus.objects.get(status='started')
            st_droppedoff = RideStatus.objects.get(status='dropped-off')
            st_cancelled  = RideStatus.objects.get(status='cancelled')
        except RideStatus.DoesNotExist as e:
            self.stdout.write(self.style.ERROR(f'Status missing: {e}. Run seed_ride_status first.'))
            return

        now = timezone.now()

        # GPS coords spread across Miami area for distance-sort testing
        rides_data = [
            # (status, rider, driver, pickup_lat, pickup_lon, dropoff_lat, dropoff_lon, pickup_time_offset_hours)
            (st_requested,  rider1, None,    25.7617, -80.1918, 25.7749, -80.1977, +2),   # future, no driver yet
            (st_enroute,    rider1, driver1, 25.7743, -80.1937, 25.7890, -80.2100, +1),   # upcoming
            (st_pickedup,   rider2, driver1, 25.7500, -80.2500, 25.7600, -80.2300, -1),   # started 1h ago
            (st_started,    rider2, driver2, 25.7800, -80.1800, 25.8000, -80.1600, -2),   # in progress
            (st_droppedoff, rider3, driver2, 25.7300, -80.2700, 25.7100, -80.2900, -4),   # completed today
            (st_droppedoff, rider3, driver3, 25.7650, -80.2050, 25.7900, -80.2200, -6),   # completed today
            (st_cancelled,  rider1, None,    25.7420, -80.3100, 25.7550, -80.2800, -3),   # cancelled, no driver
            (st_requested,  rider2, None,    25.7900, -80.1400, 25.8100, -80.1200, +3),   # future request
            (st_enroute,    rider3, driver3, 25.7100, -80.3300, 25.6900, -80.3500, +1),   # upcoming driver3
            (st_droppedoff, rider1, driver1, 25.7200, -80.3000, 25.7000, -80.3200, -30),  # old ride (30h ago)
        ]

        created_count = 0
        for (status, rider, driver, plat, plon, dlat, dlon, hours) in rides_data:
            ride, created = Ride.objects.get_or_create(
                id_rider=rider,
                status=status,
                pickup_latitude=plat,
                pickup_longitude=plon,
                defaults={
                    'id_driver': driver,
                    'dropoff_latitude': dlat,
                    'dropoff_longitude': dlon,
                    'pickup_time': now + timedelta(hours=hours),
                }
            )
            if not created:
                self.stdout.write(f'  Skipped (already exists): Ride {ride.id_ride}')
                continue

            created_count += 1

            # Add ride events — mix of recent (<24h) and old (>24h)
            # Recent events (within last 24h) — should appear in todays_ride_events
            Ride_Event.objects.create(
                id_ride=ride,
                description=f'Status set to {status.status}',
            )
            if status.status in ('en-route', 'picked-up', 'started', 'dropped-off'):
                Ride_Event.objects.create(
                    id_ride=ride,
                    description='Driver acknowledged the ride.',
                )

            # Old event (>24h ago) — should NOT appear in todays_ride_events
            old_event = Ride_Event.objects.create(
                id_ride=ride,
                description='Ride originally requested by rider.',
            )
            # Override auto_now_add by updating directly
            Ride_Event.objects.filter(pk=old_event.pk).update(
                created_at=now - timedelta(hours=48)
            )

            self.stdout.write(self.style.SUCCESS(
                f'  Created: Ride {ride.id_ride} | {rider.email} | {status.status}'
            ))

        self.stdout.write(self.style.SUCCESS(f'\nDone. {created_count} ride(s) created.'))
