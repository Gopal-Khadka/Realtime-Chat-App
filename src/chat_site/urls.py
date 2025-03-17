from django.urls import path, include

from .views import chat_view

urlpatterns = [
    path("", chat_view, name="chat_home"),
]
