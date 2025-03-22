import json
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from django.template.loader import render_to_string
from django.shortcuts import get_object_or_404

from .models import ChatGroup, GroupMessage, UserChannel


class ChatroomConsumer(WebsocketConsumer):
    """
    ChatroomConsumer handles WebSocket connections for a chatroom.
    It manages user connections, message sending, and receiving in real-time.
    """

    def connect(self):
        """
        Handles the WebSocket connection process.

        This method is called when a WebSocket connection is established.
        It retrieves the chatroom name from the URL, fetches the corresponding
        ChatGroup object, and adds the user to the chatroom group in the channel layer.
        """
        self.user = self.scope["user"]  # Get the user from the scope
        self.chatroom_name = self.scope["url_route"]["kwargs"][
            "chatroom_name"
        ]  # Get chatroom name from URL
        self.chatroom = get_object_or_404(
            ChatGroup, group_name=self.chatroom_name
        )  # Fetch the ChatGroup

        # Add the user to the chatroom group in the channel layer
        async_to_sync(self.channel_layer.group_add)(
            self.chatroom_name, self.channel_name
        )

        if self.chatroom.groupchat_name:
            UserChannel.objects.get_or_create(
                member=self.user, group=self.chatroom, channel=self.channel_name
            )
        # Update online users value
        if self.user not in self.chatroom.users_online.all():
            self.chatroom.users_online.add(self.user)
            self.update_online_count()
        self.accept()  # Accept the WebSocket connection

    def receive(self, text_data=None, bytes_data=None):
        """
        Receives messages sent from the WebSocket.

        This method is called when a message is received from the WebSocket.
        It parses the incoming JSON data, creates a new GroupMessage object,
        and sends the message to the chatroom group for broadcasting.

        Args:
            text_data (str): The text data received from the WebSocket.
            bytes_data (bytes): The binary data received from the WebSocket (not used here).
        """
        text_data_json = json.loads(text_data)  # Parse the incoming JSON data
        body = text_data_json["body"]  # Extract the message body
        message = GroupMessage.objects.create(
            body=body, author=self.user, group=self.chatroom
        )  # Create a new GroupMessage instance

        # Prepare the event to send to the group
        # Calls message_handler function defined below
        event = {"type": "message_handler", "message": message}
        async_to_sync(self.channel_layer.group_send)(
            self.chatroom_name, event
        )  # Send the event to the group

    def message_handler(self, event):
        """
        Handles the message event sent to the chatroom group.

        This method is called when a message event is received from the channel layer.
        It renders the message using a template and sends it back to the WebSocket.

        Args:
            event (dict): The event data containing the message to be sent.
        """
        message = event["message"]  # Extract the message from the event

        # Prepare the context for rendering the message
        context = {"message": message, "user": self.user}
        html = render_to_string(
            "chat_site/partials/chat_message_p.html", context=context
        )  # Render the message using a template
        self.send(text_data=html)  # Send the rendered message back to the WebSocket

    def disconnect(self, code):
        """
        Handles the WebSocket disconnection process.

        This method is called when the WebSocket connection is closed.
        It removes the user from the chatroom group in the channel layer.

        Args:
            code (int): The disconnection code.
        """
        async_to_sync(self.channel_layer.group_discard)(
            self.chatroom_name, self.channel_name
        )  # Remove the user from the chatroom group

        try:
            user_channel = UserChannel.objects.get(channel=self.channel_name)
            user_channel.delete()
        except:
            pass

        if self.user in self.chatroom.users_online.all():
            self.chatroom.users_online.remove(self.user)
            self.update_online_count()

    def online_count_handler(self, event):
        online_count = event["online_count"]
        context = {
            "online_count": online_count,
            "chat_group": self.chatroom,
        }
        html = render_to_string("chat_site/partials/online_count.html", context)
        self.send(text_data=html)

    def update_online_count(self):
        online_count = self.chatroom.users_online.count() - 1
        # event is message sent back to the browser
        event = {
            "type": "online_count_handler",  # function to handle event
            "online_count": online_count,
        }
        async_to_sync(self.channel_layer.group_send)(self.chatroom_name, event)


class OnlineStatusConsumer(WebsocketConsumer):
    def connect(self):
        self.user = self.scope["user"]
        self.group_name = "online-status"
        self.group = get_object_or_404(ChatGroup, group_name=self.group_name)

        if self.user not in self.group.users_online.all():
            self.group.users_online.add(self.user)

        async_to_sync(self.channel_layer.group_add)(self.group_name, self.channel_name)
        self.accept()
        self.online_status()

    def online_status_handler(self, event):
        online_users = self.group.users_online.exclude(id=self.user.id)
        public_chat_users = ChatGroup.objects.get(
            group_name="public-chat"
        ).users_online.exclude(id=self.user.id)

        online_in_chats = False

        my_chats: list[ChatGroup] = self.user.chat_groups.all()
        private_chats_with_users = [
            chat
            for chat in my_chats
            if chat.users_online.exclude(id=self.user.id).exists()
        ]

        if public_chat_users or private_chats_with_users:
            online_in_chats = True

        context = {"online_users": online_users, "online_in_chats": online_in_chats}
        html = render_to_string(
            "chat_site/partials/online_status.html", context=context
        )
        self.send(text_data=html)

    def online_status(self):
        event = {"type": "online_status_handler"}
        async_to_sync(self.channel_layer.group_send)(self.group_name, event)

    def disconnect(self, code):
        if self.user in self.group.users_online.all():
            self.group.users_online.remove(self.user)
        async_to_sync(self.channel_layer.group_discard)(
            self.group_name, self.channel_name
        )
        self.online_status()

    def receive(self, text_data=None, bytes_data=None):
        # Handle unexpected message types
        print("Received message:", text_data)
