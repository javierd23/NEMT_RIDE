from user_auth.models import UserRoles 
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Seed the UserRoles model with initial data'

    def handle(self, *args, **kwargs):
        roles = [
            'rider',
            'driver',
            'dispatcher',
            'admin',
        ]

        for role in roles:
            UserRoles.objects.get_or_create(role=role)

        self.stdout.write(self.style.SUCCESS('Successfully seeded UserRoles model'))