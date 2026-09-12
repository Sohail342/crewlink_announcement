from django.contrib.auth.hashers import UNUSABLE_PASSWORD_PREFIX
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import User
from apps.announcements.models import Announcement, AnnouncementRecipient
from apps.locals.models import Local, Member

DEMO_PASSWORD = "demo-password"
CLASSIFICATIONS = ("electrician", "plumber", "carpenter", "operator")

LARGE_LOCAL_NAME = "Local 100"
SMALL_LOCAL_NAME = "Local 200"
LARGE_MEMBER_COUNT = 2000
SMALL_MEMBER_COUNT = 200

SENT_ANNOUNCEMENT_TITLE = "Saturday overtime callout"

DEMO_ACCOUNTS = (
    {
        "email": "leader@local100.example",
        "role": User.Role.LEADERSHIP,
        "local_name": LARGE_LOCAL_NAME,
        "member": None,
    },
    {
        "email": "member@local100.example",
        "role": User.Role.MEMBER,
        "local_name": LARGE_LOCAL_NAME,
        "member": {
            "full_name": "Alex Rivera",
            "classification": "electrician",
            "status": Member.Status.ACTIVE,
        },
    },
    {
        "email": "leader@local200.example",
        "role": User.Role.LEADERSHIP,
        "local_name": SMALL_LOCAL_NAME,
        "member": None,
    },
    {
        "email": "member@local200.example",
        "role": User.Role.MEMBER,
        "local_name": SMALL_LOCAL_NAME,
        "member": {
            "full_name": "Jordan Hale",
            "classification": "plumber",
            "status": Member.Status.ACTIVE,
        },
    },
)


def _status_for_index(index):
    remainder = index % 20
    if remainder == 0:
        return Member.Status.RETIRED
    if remainder == 1:
        return Member.Status.SUSPENDED
    return Member.Status.ACTIVE


class Command(BaseCommand):
    help = (
        "Seed two locals, members, demo leadership/member logins, and one "
        "already-sent announcement for isolation testing."
    )

    def handle(self, *args, **options):
        with transaction.atomic():
            locals_by_name = self._seed_locals()
            demo_users = self._seed_demo_accounts(locals_by_name)
            self._seed_members(
                locals_by_name[LARGE_LOCAL_NAME],
                LARGE_MEMBER_COUNT,
                "local100",
            )
            self._seed_members(
                locals_by_name[SMALL_LOCAL_NAME],
                SMALL_MEMBER_COUNT,
                "local200",
            )
            self._seed_sent_announcement(
                locals_by_name[LARGE_LOCAL_NAME],
                demo_users["leader@local100.example"],
            )

        self._print_credentials(locals_by_name)

    def _seed_locals(self):
        locals_by_name = {}
        for name in (LARGE_LOCAL_NAME, SMALL_LOCAL_NAME):
            local, created = Local.objects.get_or_create(name=name)
            locals_by_name[name] = local
            action = "Created" if created else "Found"
            self.stdout.write(f"{action} {name} (id={local.id})")
        return locals_by_name

    def _seed_demo_accounts(self, locals_by_name):
        users = {}
        for account in DEMO_ACCOUNTS:
            local = locals_by_name[account["local_name"]]
            user, created = User.objects.get_or_create(
                email=account["email"],
                defaults={
                    "role": account["role"],
                    "local": local,
                },
            )
            if created:
                user.set_password(DEMO_PASSWORD)
                user.save(update_fields=["password"])
            else:
                user.role = account["role"]
                user.local = local
                user.set_password(DEMO_PASSWORD)
                user.save(update_fields=["password", "role", "local"])

            member_defaults = account["member"]
            if member_defaults:
                Member.objects.get_or_create(
                    user=user,
                    local=local,
                    defaults={
                        "full_name": member_defaults["full_name"],
                        "email": user.email,
                        "classification": member_defaults["classification"],
                        "status": member_defaults["status"],
                    },
                )
            users[user.email] = user
            action = "Created" if created else "Updated"
            self.stdout.write(f"{action} demo user {user.email} ({user.role})")
        return users

    def _seed_members(self, local, target_count, email_slug):
        existing = local.members.count()
        if existing >= target_count:
            self.stdout.write(
                f"{local.name} already has {existing} members; skipping bulk seed."
            )
            return

        to_create = target_count - existing
        start = existing + 1
        unusable_password = f"{UNUSABLE_PASSWORD_PREFIX}seed"
        users = [
            User(
                email=f"m{index:04d}@{email_slug}.example",
                password=unusable_password,
                role=User.Role.MEMBER,
                local=local,
                is_staff=False,
                is_superuser=False,
                is_active=True,
            )
            for index in range(start, start + to_create)
        ]
        created_users = User.objects.bulk_create(users, batch_size=500)
        members = [
            Member(
                local=local,
                user=user,
                full_name=f"Member {index:04d}",
                email=user.email,
                classification=CLASSIFICATIONS[(index - 1) % len(CLASSIFICATIONS)],
                status=_status_for_index(index),
            )
            for index, user in enumerate(created_users, start=start)
        ]
        Member.objects.bulk_create(members, batch_size=500)
        self.stdout.write(f"Added {to_create} members to {local.name}.")

    def _seed_sent_announcement(self, local, created_by):
        announcement, created = Announcement.objects.get_or_create(
            local=local,
            title=SENT_ANNOUNCEMENT_TITLE,
            defaults={
                "created_by": created_by,
                "body": (
                    "We need additional crew for Saturday overtime. "
                    "Active members should read and acknowledge."
                ),
                "push_preview": "Saturday overtime — please acknowledge",
                "needs_ack": True,
                "status": Announcement.Status.SENT,
                "sent_at": timezone.now(),
            },
        )
        if not created:
            self.stdout.write(
                f"Found existing announcement {announcement.id}; ensuring recipients."
            )

        active_members = Member.objects.filter(
            local=local,
            status=Member.Status.ACTIVE,
        ).order_by("id")
        existing_member_ids = set(
            announcement.recipients.values_list("member_id", flat=True)
        )
        now = announcement.sent_at or timezone.now()
        recipients = []
        for position, member in enumerate(active_members):
            if member.id in existing_member_ids:
                continue
            read_at = now if position % 5 == 0 else None
            acknowledged_at = (
                now if announcement.needs_ack and position % 10 == 0 else None
            )
            if acknowledged_at and not read_at:
                read_at = now
            recipients.append(
                AnnouncementRecipient(
                    announcement=announcement,
                    member=member,
                    delivery_status=AnnouncementRecipient.DeliveryStatus.SENT,
                    sent_at=now,
                    read_at=read_at,
                    acknowledged_at=acknowledged_at,
                )
            )
        if recipients:
            AnnouncementRecipient.objects.bulk_create(
                recipients,
                batch_size=500,
                ignore_conflicts=True,
            )
        self.stdout.write(
            f"{'Created' if created else 'Updated'} sent announcement "
            f"{announcement.id} with {announcement.recipients.count()} recipients."
        )

    def _print_credentials(self, locals_by_name):
        large = locals_by_name[LARGE_LOCAL_NAME]
        small = locals_by_name[SMALL_LOCAL_NAME]
        self.stdout.write("")
        self.stdout.write("Demo credentials (password for all: demo-password)")
        self.stdout.write(
            f"  {LARGE_LOCAL_NAME} (id={large.id}, ~{LARGE_MEMBER_COUNT} members)"
        )
        self.stdout.write("    leader@local100.example  LEADERSHIP")
        self.stdout.write("    member@local100.example  MEMBER")
        self.stdout.write(
            f"  {SMALL_LOCAL_NAME} (id={small.id}, ~{SMALL_MEMBER_COUNT} members)"
        )
        self.stdout.write("    leader@local200.example  LEADERSHIP")
        self.stdout.write("    member@local200.example  MEMBER")
        self.stdout.write("Classifications: electrician, plumber, carpenter, operator")
        self.stdout.write(
            f"Already-sent announcement in {LARGE_LOCAL_NAME}: "
            f"{SENT_ANNOUNCEMENT_TITLE!r}"
        )
