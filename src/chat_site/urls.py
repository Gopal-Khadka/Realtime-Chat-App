from django.urls import path, include

from .views import chat_view, get_or_create_chatroom,create_groupchat

urlpatterns = [
    path("", chat_view, name="chat_home"),
    path("chat/<username>", get_or_create_chatroom, name="start-chat"),
    path("chat/room/<chatroom_name>", chat_view, name="chatroom"),
    path("chat/new_groupchat/",create_groupchat,name="new-groupchat")
]
