from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, Http404

from .models import ChatGroup
from .forms import ChatMessageCreateForm, NewGroupForm

User = get_user_model()


@login_required
def chat_view(request: HttpRequest, chatroom_name="public-chat"):
    chat_group = get_object_or_404(ChatGroup, group_name=chatroom_name)
    chat_messages = chat_group.chat_messages.order_by("created")[:30]
    form = ChatMessageCreateForm()
    other_user = get_other_user(request.user, chat_group)

    # Add user to chat group if not already a member
    add_user_to_chat_group(request.user, chat_group)

    # Handle message saving if HTMX request
    if request.htmx:
        return handle_htmx_message(request, form, chat_group)

    context = {
        "chat_messages": chat_messages,
        "form": form,
        "other_user": other_user,
        "chatroom_name": chatroom_name,
        "chat_group": chat_group,
    }

    return render(request, "chat_site/chat.html", context)


def get_other_user(current_user, chat_group):
    """Return the other user in a private chat group."""
    if chat_group.is_private:
        if current_user not in chat_group.members.all():
            raise Http404("You are not a member of this chat group.")
        return next(
            (member for member in chat_group.members.all() if member != current_user),
            None,
        )
    return None


def add_user_to_chat_group(user, chat_group):
    """Add user to the chat group if not already a member."""
    if chat_group.groupchat_name and user not in chat_group.members.all():
        chat_group.members.add(user)


def handle_htmx_message(request, form, chat_group):
    """Handle the message creation for HTMX requests."""
    form = ChatMessageCreateForm(request.POST)
    if form.is_valid():
        message = form.save(commit=False)
        message.author = request.user
        message.group = chat_group
        message.save()
        context = {"message": message, "user": request.user}
        return render(
            request, "chat_site/partials/chat_message_p.html", context=context
        )
    return render(
        request, "chat_site/chat.html", {"form": form}
    )  # Return form errors if invalid


@login_required
def get_or_create_chatroom(request: HttpRequest, username: str):
    if request.user.username == username:
        return redirect("chat_home")

    other_user = User.objects.get(username=username)
    my_private_chatrooms = request.user.chat_groups.filter(is_private=True)

    if my_private_chatrooms.exists():
        for chatroom in my_private_chatrooms:
            if other_user in chatroom.members.all():
                return redirect("chatroom", chatroom.group_name)

    chatroom = ChatGroup.objects.create(is_private=True)
    chatroom.members.add(other_user, request.user)
    return redirect("chatroom", chatroom.group_name)


@login_required
def create_groupchat(request: HttpRequest):
    form = NewGroupForm()
    if request.method == "POST":
        form = NewGroupForm(request.POST)
        if form.is_valid():
            new_groupchat = form.save(commit=False)
            new_groupchat.admin = request.user
            new_groupchat.save()
            new_groupchat.members.add(request.user)
            return redirect("chatroom", new_groupchat.group_name)
    return render(request, "chat_site/create_groupchat.html", {"form": form})
