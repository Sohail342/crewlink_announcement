from django.contrib import admin

from apps.locals.models import Local, Member


@admin.register(Local)
class LocalAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ("id", "full_name", "email", "classification", "status", "local")
    list_filter = ("status", "classification", "local")
    search_fields = ("full_name", "email")
