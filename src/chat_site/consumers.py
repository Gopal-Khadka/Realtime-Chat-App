import json

from channels.generic.websocket import WebsocketConsumer
from django.template.loader import render_to_string
from django.shortcuts import get_object_or_404

from .models import ChatGroup, GroupMessage


class ChatroomConsumer(WebsocketConsumer):
    def connect(self):
        # This method handles the connection process
        # Typically used in network/socket programming or similar async operations

        # self.accept() is called to accept an incoming connection
        self.user = self.scope["user"]
        self.chatroom_name = self.scope["url_route"]["kwargs"]["chatroom_name"]
        self.chatroom = get_object_or_404(ChatGroup, group_name=self.chatroom_name)
        self.accept()

    def receive(self, text_data=None, bytes_data=None):
        # Receives data in JSON format
        text_data_json = json.loads(text_data)
        body = text_data_json["body"]  # getting message
        message = GroupMessage.objects.create(
            body=body, author=self.user, group=self.chatroom
        )
        context = {"message": message, "user": self.user}
        html = render_to_string(
            "chat_site/partials/chat_message_p.html", context=context
        )
        self.send(text_data=html)
