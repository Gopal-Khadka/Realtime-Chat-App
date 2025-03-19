from django.contrib import admin

from .models import ChatGroup, GroupMessage


@admin.register(ChatGroup)
class ChatGroupAdmin(admin.ModelAdmin):
    list_display = ("admin", "groupchat_name", "is_private", "members_count","online_count")
    filter_horizontal=["users_online","members"]
    list_filter = ("admin", "is_private")


@admin.register(GroupMessage)
class GroupMessageAdmin(admin.ModelAdmin):
    list_display = ("author", "group", "created")
    list_filter = ("author", "group")
