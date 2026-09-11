from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.announcements.models import Announcement, AnnouncementRecipient
from apps.locals.models import Local, Member


class AnnouncementIsolationTests(APITestCase):
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
        self.announcement_b = Announcement.objects.create(
            local=self.local_b,
            created_by=self.leader_b,
            title="Local B callout",
            body="Body B",
            push_preview="Preview B",
            needs_ack=True,
        )
        self.recipient_b = AnnouncementRecipient.objects.create(
            announcement=self.announcement_b,
            member=self.member_b,
        )

    def test_member_cannot_create_announcement(self):
        self.client.force_authenticate(user=self.member_user_a)
        response = self.client.post(
            reverse("announcement-list"),
            {
                "title": "Member attempt",
                "body": "Should fail",
                "push_preview": "Should fail",
                "needs_ack": False,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Announcement.objects.filter(local=self.local_a).count(), 0)

    def test_member_cannot_send_announcement(self):
        announcement = Announcement.objects.create(
            local=self.local_a,
            created_by=self.leader_a,
            title="Draft",
            body="Body",
            push_preview="Preview",
        )
        self.client.force_authenticate(user=self.member_user_a)
        response = self.client.post(
            reverse("announcement-send", args=[announcement.id])
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        announcement.refresh_from_db()
        self.assertEqual(announcement.status, Announcement.Status.DRAFT)

    def test_leadership_cannot_read_other_local_announcements(self):
        self.client.force_authenticate(user=self.leader_a)
        list_response = self.client.get(reverse("announcement-list"))
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(list_response.data, [])

        detail_response = self.client.get(
            reverse("announcement-detail", args=[self.announcement_b.id])
        )
        self.assertEqual(detail_response.status_code, status.HTTP_404_NOT_FOUND)

    def test_leadership_cannot_read_other_local_recipients(self):
        self.client.force_authenticate(user=self.leader_a)
        list_response = self.client.get(reverse("recipient-list"))
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(list_response.data, [])

        detail_response = self.client.get(
            reverse("recipient-detail", args=[self.recipient_b.id])
        )
        self.assertEqual(detail_response.status_code, status.HTTP_404_NOT_FOUND)

    def test_member_cannot_read_other_local_announcements_or_recipients(self):
        self.client.force_authenticate(user=self.member_user_a)
        announcement_response = self.client.get(
            reverse("announcement-detail", args=[self.announcement_b.id])
        )
        self.assertEqual(announcement_response.status_code, status.HTTP_404_NOT_FOUND)

        recipient_response = self.client.get(
            reverse("recipient-detail", args=[self.recipient_b.id])
        )
        self.assertEqual(recipient_response.status_code, status.HTTP_404_NOT_FOUND)

    def test_duplicate_send_does_not_create_duplicate_recipients(self):
        self.client.force_authenticate(user=self.leader_a)
        create_response = self.client.post(
            reverse("announcement-list"),
            {
                "title": "Callout",
                "body": "Please report",
                "push_preview": "Please report",
                "needs_ack": True,
            },
            format="json",
        )
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        announcement_id = create_response.data["id"]

        first_send = self.client.post(
            reverse("announcement-send", args=[announcement_id])
        )
        self.assertEqual(first_send.status_code, status.HTTP_200_OK)
        self.assertEqual(first_send.data["status"], Announcement.Status.QUEUED)
        self.assertEqual(
            AnnouncementRecipient.objects.filter(
                announcement_id=announcement_id
            ).count(),
            1,
        )

        second_send = self.client.post(
            reverse("announcement-send", args=[announcement_id])
        )
        self.assertEqual(second_send.status_code, status.HTTP_200_OK)
        self.assertEqual(
            AnnouncementRecipient.objects.filter(
                announcement_id=announcement_id
            ).count(),
            1,
        )

    def test_send_scopes_recipients_to_own_local_active_members(self):
        retired = User.objects.create_user(
            email="retired@a.example",
            password="password123",
            role=User.Role.MEMBER,
            local=self.local_a,
        )
        Member.objects.create(
            local=self.local_a,
            user=retired,
            full_name="Retired A",
            email="retired@a.example",
            classification="electrician",
            status=Member.Status.RETIRED,
        )
        announcement = Announcement.objects.create(
            local=self.local_a,
            created_by=self.leader_a,
            title="Active only",
            body="Body",
            push_preview="Preview",
        )
        self.client.force_authenticate(user=self.leader_a)
        response = self.client.post(
            reverse("announcement-send", args=[announcement.id])
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        recipient_member_ids = list(
            AnnouncementRecipient.objects.filter(announcement=announcement).values_list(
                "member_id", flat=True
            )
        )
        self.assertEqual(recipient_member_ids, [self.member_a.id])
