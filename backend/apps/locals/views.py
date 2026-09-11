from rest_framework import viewsets

from apps.accounts.permissions import (
    IsLeadership,
    IsLeadershipOrMember,
    LocalScopedQuerySetMixin,
)
from apps.locals.models import Local, Member
from apps.locals.serializers import LocalSerializer, MemberSerializer


class LocalViewSet(LocalScopedQuerySetMixin, viewsets.ReadOnlyModelViewSet):
    queryset = Local.objects.all()
    serializer_class = LocalSerializer
    permission_classes = [IsLeadershipOrMember]
    local_filter_field = "id"


class MemberViewSet(LocalScopedQuerySetMixin, viewsets.ReadOnlyModelViewSet):
    queryset = Member.objects.all()
    serializer_class = MemberSerializer
    permission_classes = [IsLeadership]
    local_filter_field = "local_id"
