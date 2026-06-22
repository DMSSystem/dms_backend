# users/tests.py
# pyrefly: ignore [missing-import]
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from .models import User


# ══════════════════════════════════════════════════════════════
# MODEL TESTS
# ══════════════════════════════════════════════════════════════

class UserModelTest(TestCase):

    def setUp(self):
        self.admin = User.objects.create_user(
            username='admin1', email='admin@dms.com',
            password='Admin@1234', role='admin',
            first_name='Alice', last_name='Kamau'
        )
        self.officer = User.objects.create_user(
            username='officer1', email='officer@dms.com',
            password='Officer@1234', role='officer'
        )
        self.parent = User.objects.create_user(
            username='parent1', email='parent@dms.com',
            password='Parent@1234', role='parent'
        )

    def test_str_representation(self):
        self.assertEqual(str(self.admin), 'admin1 (Administrator)')
        self.assertEqual(str(self.officer), 'officer1 (Boarding Officer)')
        self.assertEqual(str(self.parent), 'parent1 (Parent/Guardian)')

    def test_role_properties(self):
        self.assertTrue(self.admin.is_admin)
        self.assertFalse(self.admin.is_officer)
        self.assertFalse(self.admin.is_parent)

        self.assertTrue(self.officer.is_officer)
        self.assertFalse(self.officer.is_admin)

        self.assertTrue(self.parent.is_parent)
        self.assertFalse(self.parent.is_admin)

    def test_full_name_property(self):
        self.assertEqual(self.admin.full_name, 'Alice Kamau')
        # Falls back to username when no name set
        self.assertEqual(self.officer.full_name, 'officer1')

    def test_default_role_is_parent(self):
        user = User.objects.create_user(username='noRole', password='Test@1234')
        self.assertEqual(user.role, 'parent')

    def test_user_is_active_by_default(self):
        self.assertTrue(self.admin.is_active)


# ══════════════════════════════════════════════════════════════
# AUTHENTICATION TESTS
# ══════════════════════════════════════════════════════════════

class AuthenticationTest(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', email='test@dms.com',
            password='Test@1234', role='officer'
        )
        self.token_url = reverse('token_obtain_pair')
        self.refresh_url = reverse('token_refresh')
        self.verify_url = reverse('token_verify')

    def test_obtain_token_with_valid_credentials(self):
        res = self.client.post(self.token_url, {
            'username': 'testuser', 'password': 'Test@1234'
        })
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('access', res.data)
        self.assertIn('refresh', res.data)

    def test_obtain_token_with_invalid_credentials(self):
        res = self.client.post(self.token_url, {
            'username': 'testuser', 'password': 'wrongpassword'
        })
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_token(self):
        res = self.client.post(self.token_url, {
            'username': 'testuser', 'password': 'Test@1234'
        })
        refresh = res.data['refresh']
        res2 = self.client.post(self.refresh_url, {'refresh': refresh})
        self.assertEqual(res2.status_code, status.HTTP_200_OK)
        self.assertIn('access', res2.data)

    def test_inactive_user_cannot_login(self):
        self.user.is_active = False
        self.user.save()
        res = self.client.post(self.token_url, {
            'username': 'testuser', 'password': 'Test@1234'
        })
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


# ══════════════════════════════════════════════════════════════
# USER API TESTS
# ══════════════════════════════════════════════════════════════

class UserAPITest(APITestCase):

    def setUp(self):
        self.client = APIClient()

        # Create users
        self.admin = User.objects.create_user(
            username='admin', email='admin@dms.com',
            password='Admin@1234', role='admin'
        )
        self.officer = User.objects.create_user(
            username='officer', email='officer@dms.com',
            password='Officer@1234', role='officer'
        )
        self.parent = User.objects.create_user(
            username='parent', email='parent@dms.com',
            password='Parent@1234', role='parent'
        )

        # URLs
        self.list_url = reverse('user-list')
        self.me_url = reverse('user-me')
        self.change_pw_url = reverse('user-change-password')

    def _auth(self, user):
        """Authenticate client as the given user."""
        res = self.client.post(reverse('token_obtain_pair'), {
            'username': user.username,
            'password': user.username.capitalize() + '@1234'
        })
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {res.data['access']}")

    # ── List ────────────────────────────────────────────────

    def test_admin_can_list_users(self):
        self._auth(self.admin)
        res = self.client.get(self.list_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_officer_cannot_list_users(self):
        self._auth(self.officer)
        res = self.client.get(self.list_url)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_parent_cannot_list_users(self):
        self._auth(self.parent)
        res = self.client.get(self.list_url)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_cannot_list_users(self):
        res = self.client.get(self.list_url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    # ── Create ──────────────────────────────────────────────

    def test_admin_can_create_user(self):
        self._auth(self.admin)
        res = self.client.post(self.list_url, {
            'username': 'newuser',
            'email': 'new@dms.com',
            'first_name': 'New',
            'last_name': 'User',
            'role': 'officer',
            'password': 'NewPass@1234',
            'confirm_password': 'NewPass@1234',
        })
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_create_user_passwords_mismatch(self):
        self._auth(self.admin)
        res = self.client.post(self.list_url, {
            'username': 'baduser',
            'email': 'bad@dms.com',
            'role': 'officer',
            'password': 'Pass@1234',
            'confirm_password': 'Different@1234',
        })
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('confirm_password', res.data)

    def test_create_user_duplicate_email(self):
        self._auth(self.admin)
        res = self.client.post(self.list_url, {
            'username': 'anotheruser',
            'email': 'admin@dms.com',  # Already exists
            'role': 'officer',
            'password': 'Pass@1234',
            'confirm_password': 'Pass@1234',
        })
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_officer_cannot_create_user(self):
        self._auth(self.officer)
        res = self.client.post(self.list_url, {
            'username': 'hackuser', 'email': 'hack@dms.com',
            'role': 'admin', 'password': 'Pass@1234',
            'confirm_password': 'Pass@1234',
        })
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    # ── Me endpoint ─────────────────────────────────────────

    def test_me_returns_current_user(self):
        self._auth(self.officer)
        res = self.client.get(self.me_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['username'], 'officer')
        self.assertEqual(res.data['role'], 'officer')

    def test_me_does_not_expose_password(self):
        self._auth(self.officer)
        res = self.client.get(self.me_url)
        self.assertNotIn('password', res.data)

    # ── Password change ─────────────────────────────────────

    def test_user_can_change_own_password(self):
        self._auth(self.officer)
        res = self.client.post(self.change_pw_url, {
            'old_password': 'Officer@1234',
            'new_password': 'NewOfficer@5678',
            'confirm_new_password': 'NewOfficer@5678',
        })
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.officer.refresh_from_db()
        self.assertTrue(self.officer.check_password('NewOfficer@5678'))

    def test_wrong_old_password_rejected(self):
        self._auth(self.officer)
        res = self.client.post(self.change_pw_url, {
            'old_password': 'WrongPassword',
            'new_password': 'NewPass@1234',
            'confirm_new_password': 'NewPass@1234',
        })
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    # ── Deactivate / Activate ───────────────────────────────

    def test_admin_can_deactivate_user(self):
        self._auth(self.admin)
        url = reverse('user-deactivate', args=[self.officer.id])
        res = self.client.post(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.officer.refresh_from_db()
        self.assertFalse(self.officer.is_active)

    def test_admin_cannot_deactivate_self(self):
        self._auth(self.admin)
        url = reverse('user-deactivate', args=[self.admin.id])
        res = self.client.post(url)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_admin_can_activate_user(self):
        self.officer.is_active = False
        self.officer.save()
        self._auth(self.admin)
        url = reverse('user-activate', args=[self.officer.id])
        res = self.client.post(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.officer.refresh_from_db()
        self.assertTrue(self.officer.is_active)

    # ── Filter by role ──────────────────────────────────────

    def test_admin_can_filter_users_by_role(self):
        self._auth(self.admin)
        res = self.client.get(reverse('user-by-role') + '?role=officer')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        for u in res.data:
            self.assertEqual(u['role'], 'officer')

    def test_filter_invalid_role_returns_400(self):
        self._auth(self.admin)
        res = self.client.get(reverse('user-by-role') + '?role=superuser')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    # ── Admin password reset ────────────────────────────────

    def test_admin_can_reset_user_password(self):
        self._auth(self.admin)
        url = reverse('user-reset-password', args=[self.officer.id])
        res = self.client.post(url, {'new_password': 'Reset@9999'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.officer.refresh_from_db()
        self.assertTrue(self.officer.check_password('Reset@9999'))