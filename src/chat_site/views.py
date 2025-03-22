from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, Http404, HttpResponse

from .models import ChatGroup, UserChannel, GroupMessage
from .forms import ChatMessageCreateForm, NewGroupForm, ChatRoomEditForm

User = get_user_model()


@login_required
def chat_view(request: HttpRequest, chatroom_name="public-chat"):
    chat_group:list[ChatGroup] = get_object_or_404(ChatGroup, group_name=chatroom_name)
    chat_messages = chat_group.chat_messages.all()[:40:-1]
    form = ChatMessageCreateForm()
    other_user = get_other_user(request.user, chat_group)

    # Add user to chat group if not already a member
    is_user_added = add_user_to_chat_group(request, chat_group)
    if is_user_added is False:
        return redirect("profile-settings")

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


def add_user_to_chat_group(request: HttpRequest, chat_group: ChatGroup):
    """
    Add user to the chat group if not already a member.
    Checks if the email is verified or not.
    Non-verified members can't join chat.
    """
    if chat_group.groupchat_name and request.user not in chat_group.members.all():
        if request.user.emailaddress_set.filter(verified=True).exists():
            chat_group.members.add(request.user)
            return True
        messages.warning(request, "You need to verify your email first to join in.")
        return False


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


@login_required
def chatroom_edit_view(request: HttpRequest, chatroom_name: str):
    chatgroup = get_object_or_404(ChatGroup, group_name=chatroom_name)
    if chatgroup.admin != request.user:
        messages.warning(request, "You need to be admin of chat to access this feature")
        raise Http404("You need to be admin of chat to access this feature")

    form = ChatRoomEditForm(instance=chatgroup)

    if request.method == "POST":
        form = ChatRoomEditForm(request.POST, instance=chatgroup)
        if form.is_valid():
            form.save()

            remove_members = request.POST.getlist("remove_members")
            for member_id in remove_members:
                channel_layer = get_channel_layer()
                member = User.objects.get(id=member_id)
                user_channels = UserChannel.objects.filter(
                    member=member, group=chatgroup
                )
                for user_channel in user_channels:
                    async_to_sync(channel_layer.group_discard)(
                        chatroom_name, user_channel.channel
                    )
                    user_channel.delete()
                chatgroup.members.remove(member)

            return redirect("chatroom", chatroom_name)
    context = {
        "form": form,
        "chat_group": chatgroup,
    }
    return render(request, "chat_site/chatroom_edit.html", context)


@login_required
def chatroom_delete_view(request: HttpRequest, chatroom_name: str):
    chatgroup = get_object_or_404(ChatGroup, group_name=chatroom_name)
    if chatgroup.admin != request.user:
        raise Http404("You need to be admin of chat to access this feature")

    if request.method == "POST":
        chatgroup.delete()
        messages.success(request, "Chatroom deleted.")
        return redirect("chat_home")
    return render(request, "chat_site/chatroom_delete.html", {"chat_group": chatgroup})


@login_required
def chatroom_leave_view(request: HttpRequest, chatroom_name: str):
    chatgroup = get_object_or_404(ChatGroup, group_name=chatroom_name)
    if request.user not in chatgroup.members.all():
        raise Http404("You need to be member of chat to leave the chat.")

    if request.method == "POST":
        chatgroup.members.remove(request.user)
        messages.success(request, "You are now out of the chat room .")
        return redirect("chat_home")
    return render(request, "chat_site/chatroom_leave.html", {"chat_group": chatgroup})


@login_required
def chat_file_upload(request: HttpRequest, chatroom_name: str):
    chat_group = get_object_or_404(ChatGroup, group_name=chatroom_name)

    if request.htmx and request.FILES:
        file = request.FILES["file"]
        message = GroupMessage.objects.create(
            file=file, author=request.user, group=chat_group
        )

        channel_layer = get_channel_layer()
        event = {
            "type": "message_handler",
            "message": message,
        }

        async_to_sync(channel_layer.group_send)(chatroom_name, event)
    return HttpResponse()
