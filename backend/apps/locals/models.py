from django.conf import settings
from django.db import models


class Local(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class Member(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        RETIRED = "retired", "Retired"
        SUSPENDED = "suspended", "Suspended"

    local = models.ForeignKey(
        Local,
        on_delete=models.PROTECT,
        related_name="members",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="members",
    )
    full_name = models.CharField(max_length=255)
    email = models.EmailField()
    classification = models.CharField(max_length=255)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )

    def __str__(self):
        return self.full_name
