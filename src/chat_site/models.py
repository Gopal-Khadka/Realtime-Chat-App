import os
import shortuuid
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class ChatGroup(models.Model):
    group_name = models.CharField(max_length=128, unique=True, default=shortuuid.uuid)
    groupchat_name = models.CharField(max_length=128, null=True, blank=True)
    admin = models.ForeignKey(
        User, related_name="groupchats", blank=True, null=True, on_delete=models.CASCADE
    )
    users_online = models.ManyToManyField(
        User, related_name="online_in_groups", blank=True
    )
    members = models.ManyToManyField(User, related_name="chat_groups", blank=True)
    is_private = models.BooleanField(default=False)

    @property
    def members_count(self):
        return self.members.count()

    @property
    def online_count(self):
        return self.users_online.count()

    def __str__(self):
        return self.group_name


class GroupMessage(models.Model):
    group = models.ForeignKey(
        ChatGroup, related_name="chat_messages", on_delete=models.CASCADE
    )
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    body = models.CharField(max_length=300, blank=True, null=True)
    file = models.FileField(upload_to="files/", blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created"]

    def __str__(self):
        return f"{self.author.username} :{self.body if self.body else self.filename}"

    @property
    def filename(self):
        if self.file:
            return os.path.basename(self.file.name)
        return None

    @property
    def is_image(self):
        if self.filename.lower().endswith(
            (".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp")
        ):
            return True
        return False


class UserChannel(models.Model):
    member = models.ForeignKey(User, on_delete=models.CASCADE)
    group = models.ForeignKey(
        ChatGroup, on_delete=models.CASCADE, null=True, blank=True
    )
    channel = models.CharField(
        max_length=300
    )  # in-memory channel name filled by consumers.connect

    def __str__(self):
        return self.channel
