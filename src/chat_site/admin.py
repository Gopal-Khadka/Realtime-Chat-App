from django.contrib import admin

from .models import ChatGroup, GroupMessage

admin.site.register(ChatGroup)


@admin.register(GroupMessage)
class GroupMessageAdmin(admin.ModelAdmin):
    list_display = ("author", "group", "created")
    list_filter = ("author", "group")
