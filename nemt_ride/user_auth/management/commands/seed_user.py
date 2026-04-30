from django.core.management.base import BaseCommand
from user_auth.models import User, UserRoles


class Command(BaseCommand):
    help = 'Seed the database with test users (3 riders, 3 drivers, 1 admin)'

    def handle(self, *args, **kwargs):
        try:
            role_rider = UserRoles.objects.get(role='rider')
            role_driver = UserRoles.objects.get(role='driver')
            role_admin = UserRoles.objects.get(role='admin')
        except UserRoles.DoesNotExist:
            self.stdout.write(self.style.ERROR(
                'Roles not found. Run seed_roles first: python manage.py seed_roles'
            ))
            return

        users = [
            # Riders
            {'email': 'rider1@nemt.com', 'password': 'Rider1pass!', 'first_name': 'Alice',   'last_name': 'Smith',   'phone_number': '555-1001', 'role': role_rider},
            {'email': 'rider2@nemt.com', 'password': 'Rider2pass!', 'first_name': 'Bob',     'last_name': 'Johnson', 'phone_number': '555-1002', 'role': role_rider},
            {'email': 'rider3@nemt.com', 'password': 'Rider3pass!', 'first_name': 'Carol',   'last_name': 'Davis',   'phone_number': '555-1003', 'role': role_rider},
            # Drivers
            {'email': 'driver1@nemt.com', 'password': 'Driver1pass!', 'first_name': 'David',  'last_name': 'Wilson',  'phone_number': '555-2001', 'role': role_driver},
            {'email': 'driver2@nemt.com', 'password': 'Driver2pass!', 'first_name': 'Eva',    'last_name': 'Martinez','phone_number': '555-2002', 'role': role_driver},
            {'email': 'driver3@nemt.com', 'password': 'Driver3pass!', 'first_name': 'Frank',  'last_name': 'Garcia',  'phone_number': '555-2003', 'role': role_driver},
            # Admin
            {'email': 'admin@nemt.com',   'password': 'Admin1pass!',  'first_name': 'Grace',  'last_name': 'Lee',     'phone_number': '555-3001', 'role': role_admin, 'is_staff': True, 'is_superuser': True},
        ]

        created_count = 0
        for data in users:
            email = data.pop('email')
            password = data.pop('password')
            is_staff = data.pop('is_staff', False)
            is_superuser = data.pop('is_superuser', False)

            user, created = User.objects.get_or_create(
                email=email,
                defaults={**data, 'is_staff': is_staff, 'is_superuser': is_superuser},
            )
            if created:
                user.set_password(password)
                user.save()
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'  Created: {email} ({user.role.role})'))
            else:
                self.stdout.write(f'  Skipped (already exists): {email}')

        self.stdout.write(self.style.SUCCESS(f'\nDone. {created_count} user(s) created.'))
