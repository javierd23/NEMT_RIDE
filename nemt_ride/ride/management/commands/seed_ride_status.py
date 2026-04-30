from ride.models import RideStatus
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Seed the RideEventStatus model with initial data'

    def handle(self, *args, **kwargs):
        statuses = [
            'requested',
            'en-route',
            'picked-up',
            'started',
            'dropped-off',
            'cancelled',
        ]

        for status in statuses:
            RideStatus.objects.get_or_create(status=status)

        self.stdout.write(self.style.SUCCESS('Successfully seeded RideEventStatus model'))

 