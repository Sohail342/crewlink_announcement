from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.locals.models import Local


class AuthApiTests(APITestCase):
    def setUp(self):
        self.local = Local.objects.create(name="Local A")
        self.user = User.objects.create_user(
            email="leader@a.example",
            password="password123",
            role=User.Role.LEADERSHIP,
            local=self.local,
        )

    def test_login_returns_token(self):
        response = self.client.post(
            reverse("auth-login"),
            {"email": "leader@a.example", "password": "password123"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("token", response.data)
        self.assertEqual(response.data["user"]["email"], "leader@a.example")
        self.assertEqual(response.data["user"]["role"], User.Role.LEADERSHIP)

    def test_me_requires_authentication(self):
        response = self.client.get(reverse("auth-me"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_returns_authenticated_user(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse("auth-me"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.user.id)
        self.assertEqual(response.data["local"], self.local.id)
