from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User, UserRoles

SIGNUP_URL = '/api/v1/auth/signup/'
LOGIN_URL = '/api/v1/auth/login/'
LOGOUT_URL = '/api/v1/auth/logout/'


class BaseAuthTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        # Must match seed order so role PKs align with the model's default=3 (rider).
        cls.role_admin = UserRoles.objects.create(role='admin')   # id=1
        cls.role_driver = UserRoles.objects.create(role='driver') # id=2
        cls.role_rider = UserRoles.objects.create(role='rider')   # id=3

        cls.existing_user = User.objects.create_user(
            email='existing@test.com',
            password='strongpass1',
            role=cls.role_rider,
        )
        cls.inactive_user = User.objects.create_user(
            email='inactive@test.com',
            password='strongpass1',
            role=cls.role_rider,
            is_active=False,
        )


# ---------------------------------------------------------------------------
# SignUp
# ---------------------------------------------------------------------------

class SignUpTest(BaseAuthTestCase):
    def _payload(self, **overrides):
        data = {
            'email': 'newuser@test.com',
            'password': 'strongpass1',
            'first_name': 'Jane',
            'last_name': 'Doe',
            'phone_number': '5550001234',
        }
        data.update(overrides)
        return data

    def test_successful_signup_returns_201(self):
        response = self.client.post(SIGNUP_URL, data=self._payload(), format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_successful_signup_returns_tokens_and_user(self):
        response = self.client.post(SIGNUP_URL, data=self._payload(), format='json')
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('user', response.data)

    def test_user_profile_fields_in_response(self):
        response = self.client.post(SIGNUP_URL, data=self._payload(), format='json')
        user_data = response.data['user']
        for field in ('id_user', 'email', 'first_name', 'last_name', 'is_active', 'date_joined'):
            self.assertIn(field, user_data)

    def test_user_is_created_in_db(self):
        self.client.post(SIGNUP_URL, data=self._payload(), format='json')
        self.assertTrue(User.objects.filter(email='newuser@test.com').exists())

    def test_role_cannot_be_set_via_signup(self):
        """Users must not be able to self-assign a role at signup."""
        response = self.client.post(
            SIGNUP_URL,
            data=self._payload(**{'role': self.role_admin.pk}),
            format='json',
        )
        # Either the field is ignored (201) or rejected (400) — but never admin role assigned.
        if response.status_code == status.HTTP_201_CREATED:
            user = User.objects.get(email='newuser@test.com')
            self.assertNotEqual(user.role, self.role_admin)

    def test_duplicate_email_returns_400(self):
        response = self.client.post(
            SIGNUP_URL,
            data=self._payload(email='existing@test.com'),
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_short_password_returns_400(self):
        response = self.client.post(SIGNUP_URL, data=self._payload(password='short'), format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_email_returns_400(self):
        payload = self._payload()
        del payload['email']
        response = self.client.post(SIGNUP_URL, data=payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_email_returns_400(self):
        response = self.client.post(SIGNUP_URL, data=self._payload(email='not-an-email'), format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_is_not_returned_in_response(self):
        response = self.client.post(SIGNUP_URL, data=self._payload(), format='json')
        self.assertNotIn('password', response.data.get('user', {}))


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

class LoginTest(BaseAuthTestCase):
    def test_valid_credentials_return_200(self):
        response = self.client.post(
            LOGIN_URL,
            data={'email': 'existing@test.com', 'password': 'strongpass1'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_valid_login_returns_tokens_and_user(self):
        response = self.client.post(
            LOGIN_URL,
            data={'email': 'existing@test.com', 'password': 'strongpass1'},
            format='json',
        )
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('user', response.data)

    def test_user_profile_fields_in_login_response(self):
        response = self.client.post(
            LOGIN_URL,
            data={'email': 'existing@test.com', 'password': 'strongpass1'},
            format='json',
        )
        for field in ('id_user', 'email', 'is_active', 'date_joined'):
            self.assertIn(field, response.data['user'])

    def test_wrong_password_returns_400(self):
        response = self.client.post(
            LOGIN_URL,
            data={'email': 'existing@test.com', 'password': 'wrongpass'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_nonexistent_email_returns_400(self):
        response = self.client.post(
            LOGIN_URL,
            data={'email': 'nobody@test.com', 'password': 'strongpass1'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_inactive_user_cannot_login(self):
        response = self.client.post(
            LOGIN_URL,
            data={'email': 'inactive@test.com', 'password': 'strongpass1'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_password_returns_400(self):
        response = self.client.post(LOGIN_URL, data={'email': 'existing@test.com'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_email_returns_400(self):
        response = self.client.post(LOGIN_URL, data={'password': 'strongpass1'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# ---------------------------------------------------------------------------
# Logout
# ---------------------------------------------------------------------------

class LogoutTest(BaseAuthTestCase):
    def _get_refresh_token(self):
        return str(RefreshToken.for_user(self.existing_user))

    def _auth(self):
        self.client.force_authenticate(user=self.existing_user)

    def test_valid_logout_returns_200(self):
        self._auth()
        response = self.client.post(
            LOGOUT_URL,
            data={'refresh': self._get_refresh_token()},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_valid_logout_returns_detail_message(self):
        self._auth()
        response = self.client.post(
            LOGOUT_URL,
            data={'refresh': self._get_refresh_token()},
            format='json',
        )
        self.assertIn('detail', response.data)

    def test_blacklisted_token_cannot_be_reused(self):
        self._auth()
        token = self._get_refresh_token()
        self.client.post(LOGOUT_URL, data={'refresh': token}, format='json')
        # second logout attempt with the same token must fail
        response = self.client.post(LOGOUT_URL, data={'refresh': token}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_token_returns_400(self):
        self._auth()
        response = self.client.post(
            LOGOUT_URL,
            data={'refresh': 'this.is.not.a.valid.token'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_refresh_key_returns_400(self):
        self._auth()
        response = self.client.post(LOGOUT_URL, data={}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], 'Refresh token required.')

    def test_unauthenticated_logout_returns_401(self):
        response = self.client.post(
            LOGOUT_URL,
            data={'refresh': self._get_refresh_token()},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
