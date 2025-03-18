from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required

from .models import ChatGroup


@login_required
def chat_view(request):
    chat_group = get_object_or_404(ChatGroup, group_name="public-chat")
    chat_messages = chat_group.chat_messages.order_by("created")[:30]
    return render(request, "chat_site/chat.html", {"chat_messages": chat_messages})
