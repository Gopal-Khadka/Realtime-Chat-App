from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest
from .models import ChatGroup
from .forms import ChatMessageCreateForm


@login_required
def chat_view(request: HttpRequest):
    chat_group = get_object_or_404(ChatGroup, group_name="public-chat")
    chat_messages = chat_group.chat_messages.order_by("created")[:30]

    form = ChatMessageCreateForm()
    if request.htmx:
        form = ChatMessageCreateForm(request.POST)
        if form.is_valid():
            # before saving msg, we need to add author and chatgroup value to it
            # So commit = False
            message = form.save(commit=False)
            message.author = request.user
            message.group = chat_group
            message.save()
            context = {"message": message, "user": request.user}
            return render(
                request, "chat_site/partials/chat_message_p.html", context=context
            )

    return render(
        request, "chat_site/chat.html", {"chat_messages": chat_messages, "form": form}
    )
