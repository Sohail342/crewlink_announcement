from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.locals.models import Local, Member


class LocalIsolationTests(APITestCase):
    def setUp(self):
        self.local_a = Local.objects.create(name="Local A")
        self.local_b = Local.objects.create(name="Local B")
        self.leader_a = User.objects.create_user(
            email="leader@a.example",
            password="password123",
            role=User.Role.LEADERSHIP,
            local=self.local_a,
        )
        self.leader_b = User.objects.create_user(
            email="leader@b.example",
            password="password123",
            role=User.Role.LEADERSHIP,
            local=self.local_b,
        )
        self.member_user_a = User.objects.create_user(
            email="member@a.example",
            password="password123",
            role=User.Role.MEMBER,
            local=self.local_a,
        )
        self.member_a = Member.objects.create(
            local=self.local_a,
            user=self.member_user_a,
            full_name="Member A",
            email="member@a.example",
            classification="electrician",
            status=Member.Status.ACTIVE,
        )
        self.member_user_b = User.objects.create_user(
            email="member@b.example",
            password="password123",
            role=User.Role.MEMBER,
            local=self.local_b,
        )
        self.member_b = Member.objects.create(
            local=self.local_b,
            user=self.member_user_b,
            full_name="Member B",
            email="member@b.example",
            classification="plumber",
            status=Member.Status.ACTIVE,
        )

    def test_leadership_lists_only_own_local(self):
        self.client.force_authenticate(user=self.leader_a)
        response = self.client.get(reverse("local-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([row["id"] for row in response.data], [self.local_a.id])

    def test_leadership_cannot_retrieve_other_local(self):
        self.client.force_authenticate(user=self.leader_a)
        response = self.client.get(reverse("local-detail", args=[self.local_b.id]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_member_cannot_list_members(self):
        self.client.force_authenticate(user=self.member_user_a)
        response = self.client.get(reverse("member-list"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_leadership_cannot_read_other_local_members(self):
        self.client.force_authenticate(user=self.leader_a)
        list_response = self.client.get(reverse("member-list"))
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual([row["id"] for row in list_response.data], [self.member_a.id])

        detail_response = self.client.get(
            reverse("member-detail", args=[self.member_b.id])
        )
        self.assertEqual(detail_response.status_code, status.HTTP_404_NOT_FOUND)
