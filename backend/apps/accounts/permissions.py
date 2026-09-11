from rest_framework.permissions import BasePermission

from apps.accounts.models import User


def object_local_id(obj):
    if obj.__class__.__name__ == "Local":
        return obj.pk
    local_id = getattr(obj, "local_id", None)
    if local_id is not None:
        return local_id
    announcement = getattr(obj, "announcement", None)
    if announcement is not None:
        return announcement.local_id
    return None


def user_shares_local(user, obj):
    if not getattr(user, "local_id", None):
        return False
    return object_local_id(obj) == user.local_id


class LocalScopedQuerySetMixin:
    local_filter_field = "local_id"

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if getattr(user, "is_superuser", False):
            return queryset
        local_id = getattr(user, "local_id", None)
        if not local_id:
            return queryset.none()
        return queryset.filter(**{self.local_filter_field: local_id})


class IsLeadership(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == User.Role.LEADERSHIP
        )

    def has_object_permission(self, request, view, obj):
        return user_shares_local(request.user, obj)


class IsMemberRole(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == User.Role.MEMBER
        )

    def has_object_permission(self, request, view, obj):
        if not user_shares_local(request.user, obj):
            return False
        member = getattr(obj, "member", None)
        if member is not None:
            return member.user_id == request.user.id
        return True


class IsLeadershipOrMember(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role in (User.Role.LEADERSHIP, User.Role.MEMBER)
        )

    def has_object_permission(self, request, view, obj):
        if not user_shares_local(request.user, obj):
            return False
        if request.user.role == User.Role.MEMBER:
            member = getattr(obj, "member", None)
            if member is not None:
                return member.user_id == request.user.id
        return True
