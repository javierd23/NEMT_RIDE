from datetime import timedelta

from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from user_auth.models import User, UserRoles
from .models import Ride, RideStatus, Ride_Event

LIST_URL = '/api/v1/rides/'


def detail_url(ride_id):
    return f'/api/v1/rides/{ride_id}/'


class BaseRideTestCase(APITestCase):
    """Shared fixtures for all ride endpoint tests."""

    @classmethod
    def setUpTestData(cls):
        cls.role_admin = UserRoles.objects.create(role='admin')
        cls.role_driver = UserRoles.objects.create(role='driver')
        cls.role_rider = UserRoles.objects.create(role='rider')

        cls.status_requested = RideStatus.objects.create(status='requested')
        cls.status_en_route = RideStatus.objects.create(status='en-route')

        cls.admin = User.objects.create_user(
            email='admin@test.com', password='pass123abc', role=cls.role_admin
        )
        cls.rider = User.objects.create_user(
            email='rider@test.com', password='pass123abc', role=cls.role_rider
        )
        cls.driver = User.objects.create_user(
            email='driver@test.com', password='pass123abc', role=cls.role_driver
        )

        cls.ride1 = Ride.objects.create(
            status=cls.status_requested,
            id_rider=cls.rider,
            pickup_latitude=40.7128,
            pickup_longitude=-74.0060,
            dropoff_latitude=40.7580,
            dropoff_longitude=-73.9855,
            pickup_time=timezone.now() + timedelta(hours=1),
        )
        cls.ride2 = Ride.objects.create(
            status=cls.status_en_route,
            id_rider=cls.rider,
            id_driver=cls.driver,
            pickup_latitude=34.0522,
            pickup_longitude=-118.2437,
            dropoff_latitude=34.0195,
            dropoff_longitude=-118.4912,
            pickup_time=timezone.now() + timedelta(hours=2),
        )


# ---------------------------------------------------------------------------
# Permissions
# ---------------------------------------------------------------------------

class RidePermissionsTest(BaseRideTestCase):
    """Only admin users may access any ride endpoint."""

    def test_unauthenticated_request_is_denied(self):
        # IsAuthenticated (checked first) returns 401 when no credentials are provided.
        response = self.client.get(LIST_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_rider_is_denied(self):
        self.client.force_authenticate(user=self.rider)
        response = self.client.get(LIST_URL)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_driver_is_denied(self):
        self.client.force_authenticate(user=self.driver)
        response = self.client.get(LIST_URL)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_list_rides(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(LIST_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


# ---------------------------------------------------------------------------
# List endpoint structure
# ---------------------------------------------------------------------------

class RideListTest(BaseRideTestCase):
    """List endpoint returns all rides with correct response structure."""

    def setUp(self):
        self.client.force_authenticate(user=self.admin)

    def test_returns_all_rides(self):
        response = self.client.get(LIST_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

    def test_response_has_pagination_keys(self):
        response = self.client.get(LIST_URL)
        for key in ('count', 'next', 'previous', 'results'):
            self.assertIn(key, response.data)

    def test_ride_fields_present(self):
        response = self.client.get(LIST_URL)
        ride = response.data['results'][0]
        expected = {
            'id_ride', 'status', 'id_rider', 'id_driver',
            'pickup_latitude', 'pickup_longitude',
            'dropoff_latitude', 'dropoff_longitude',
            'pickup_time', 'todays_ride_events', 'distance_to_pickup',
        }
        self.assertEqual(set(ride.keys()), expected)

    def test_status_is_string_not_pk(self):
        response = self.client.get(LIST_URL)
        ride = next(r for r in response.data['results'] if r['id_ride'] == self.ride1.id_ride)
        self.assertIsInstance(ride['status'], str)
        self.assertEqual(ride['status'], 'requested')

    def test_default_ordering_is_descending_pickup_time(self):
        response = self.client.get(LIST_URL)
        times = [r['pickup_time'] for r in response.data['results']]
        self.assertEqual(times, sorted(times, reverse=True))


# ---------------------------------------------------------------------------
# Filtering
# ---------------------------------------------------------------------------

class RideFilterTest(BaseRideTestCase):
    """Filtering by status and rider_email."""

    def setUp(self):
        self.client.force_authenticate(user=self.admin)

    def test_filter_by_status_matches_one_ride(self):
        response = self.client.get(LIST_URL, {'status': 'requested'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id_ride'], self.ride1.id_ride)

    def test_filter_by_status_is_case_insensitive(self):
        response = self.client.get(LIST_URL, {'status': 'REQUESTED'})
        self.assertEqual(response.data['count'], 1)

    def test_filter_by_rider_email_returns_all_their_rides(self):
        response = self.client.get(LIST_URL, {'rider_email': 'rider@test.com'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

    def test_filter_by_rider_email_is_case_insensitive(self):
        response = self.client.get(LIST_URL, {'rider_email': 'RIDER@TEST.COM'})
        self.assertEqual(response.data['count'], 2)

    def test_filter_by_nonexistent_status_returns_empty(self):
        response = self.client.get(LIST_URL, {'status': 'nonexistent'})
        self.assertEqual(response.data['count'], 0)

    def test_filter_by_unknown_rider_email_returns_empty(self):
        response = self.client.get(LIST_URL, {'rider_email': 'nobody@test.com'})
        self.assertEqual(response.data['count'], 0)


# ---------------------------------------------------------------------------
# Ordering
# ---------------------------------------------------------------------------

class RideOrderingTest(BaseRideTestCase):
    """Ordering by pickup_time ascending and descending."""

    def setUp(self):
        self.client.force_authenticate(user=self.admin)

    def test_order_by_pickup_time_ascending(self):
        response = self.client.get(LIST_URL, {'ordering': 'pickup_time'})
        times = [r['pickup_time'] for r in response.data['results']]
        self.assertEqual(times, sorted(times))

    def test_order_by_pickup_time_descending(self):
        response = self.client.get(LIST_URL, {'ordering': '-pickup_time'})
        times = [r['pickup_time'] for r in response.data['results']]
        self.assertEqual(times, sorted(times, reverse=True))


# ---------------------------------------------------------------------------
# Distance annotation (lat/lon query params)
# ---------------------------------------------------------------------------

class RideDistanceAnnotationTest(BaseRideTestCase):
    """lat/lon params annotate distance_to_pickup; absent params leave it null."""

    def setUp(self):
        self.client.force_authenticate(user=self.admin)

    def test_distance_is_none_without_lat_lon(self):
        response = self.client.get(LIST_URL)
        for ride in response.data['results']:
            self.assertIsNone(ride['distance_to_pickup'])

    def test_distance_is_float_with_valid_lat_lon(self):
        response = self.client.get(LIST_URL, {'lat': '40.7128', 'lon': '-74.0060'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for ride in response.data['results']:
            self.assertIsNotNone(ride['distance_to_pickup'])
            self.assertIsInstance(ride['distance_to_pickup'], float)

    def test_distance_enables_ascending_order(self):
        response = self.client.get(
            LIST_URL, {'lat': '40.7128', 'lon': '-74.0060', 'ordering': 'distance_to_pickup'}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        distances = [r['distance_to_pickup'] for r in response.data['results']]
        self.assertEqual(distances, sorted(distances))

    def test_invalid_lat_lon_falls_back_gracefully(self):
        response = self.client.get(LIST_URL, {'lat': 'abc', 'lon': 'xyz'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for ride in response.data['results']:
            self.assertIsNone(ride['distance_to_pickup'])

    def test_only_lat_provided_skips_annotation(self):
        response = self.client.get(LIST_URL, {'lat': '40.7128'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for ride in response.data['results']:
            self.assertIsNone(ride['distance_to_pickup'])

    def test_only_lon_provided_skips_annotation(self):
        response = self.client.get(LIST_URL, {'lon': '-74.0060'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for ride in response.data['results']:
            self.assertIsNone(ride['distance_to_pickup'])


# ---------------------------------------------------------------------------
# todays_ride_events prefetch (last 24 h only)
# ---------------------------------------------------------------------------

class RideTodaysEventsTest(BaseRideTestCase):
    """todays_ride_events includes only events created in the last 24 hours."""

    def setUp(self):
        self.client.force_authenticate(user=self.admin)

    def test_recent_event_appears(self):
        Ride_Event.objects.create(id_ride=self.ride1, description='Driver assigned')
        response = self.client.get(detail_url(self.ride1.id_ride))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['todays_ride_events']), 1)
        self.assertEqual(response.data['todays_ride_events'][0]['description'], 'Driver assigned')

    def test_event_older_than_24h_is_excluded(self):
        event = Ride_Event.objects.create(id_ride=self.ride1, description='Old event')
        Ride_Event.objects.filter(pk=event.pk).update(
            created_at=timezone.now() - timedelta(hours=25)
        )
        response = self.client.get(LIST_URL)
        ride_data = next(
            r for r in response.data['results'] if r['id_ride'] == self.ride1.id_ride
        )
        self.assertEqual(len(ride_data['todays_ride_events']), 0)

    def test_no_events_returns_empty_list(self):
        response = self.client.get(detail_url(self.ride2.id_ride))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['todays_ride_events'], [])


# ---------------------------------------------------------------------------
# CRUD operations
# ---------------------------------------------------------------------------

class RideCRUDTest(BaseRideTestCase):
    """Create, retrieve, partial-update, and delete operations."""

    def setUp(self):
        self.client.force_authenticate(user=self.admin)

    def test_retrieve_single_ride(self):
        response = self.client.get(detail_url(self.ride1.id_ride))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id_ride'], self.ride1.id_ride)

    def test_create_ride(self):
        payload = {
            'id_rider': self.rider.pk,
            'pickup_latitude': 51.5074,
            'pickup_longitude': -0.1278,
            'dropoff_latitude': 51.5155,
            'dropoff_longitude': -0.0922,
            'pickup_time': (timezone.now() + timedelta(hours=3)).isoformat(),
        }
        response = self.client.post(LIST_URL, data=payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('id_ride', response.data)
        self.assertTrue(Ride.objects.filter(pk=response.data['id_ride']).exists())

    def test_partial_update_ride(self):
        new_time = (timezone.now() + timedelta(hours=5)).isoformat()
        response = self.client.patch(
            detail_url(self.ride1.id_ride),
            data={'pickup_time': new_time},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_delete_ride(self):
        ride = Ride.objects.create(
            status=self.status_requested,
            id_rider=self.rider,
            pickup_latitude=1.0, pickup_longitude=1.0,
            dropoff_latitude=2.0, dropoff_longitude=2.0,
            pickup_time=timezone.now() + timedelta(hours=4),
        )
        response = self.client.delete(detail_url(ride.id_ride))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Ride.objects.filter(pk=ride.id_ride).exists())
