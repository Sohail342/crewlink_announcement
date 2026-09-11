from rest_framework import serializers

from apps.locals.models import Local, Member


class LocalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Local
        fields = ("id", "name")
        read_only_fields = ("id", "name")


class MemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = Member
        fields = (
            "id",
            "local",
            "user",
            "full_name",
            "email",
            "classification",
            "status",
        )
        read_only_fields = (
            "id",
            "local",
            "user",
            "full_name",
            "email",
            "classification",
            "status",
        )
