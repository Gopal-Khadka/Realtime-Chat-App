from django import forms
from django.forms import ModelForm

from .models import ChatGroup, GroupMessage


class ChatMessageCreateForm(ModelForm):
    class Meta:
        model = GroupMessage
        fields = ["body"]
        widgets = {
            "body": forms.TextInput(
                attrs={
                    "placeholder": "Add Message",
                    "class": "p-4 text-black",
                    "maxlength": "300",
                    "autofocus": True,
                }
            )
        }


class NewGroupForm(ModelForm):
    class Meta:
        model = ChatGroup
        fields = ["groupchat_name"]
        widgets = {
            "groupchat_name": forms.TextInput(
                attrs={
                    "placeholder": "Enter chat name",
                    "class": "p-4 text-black",
                    "maxlength": "120",
                    "autofocus": True,
                    "required": True,
                }
            )
        }


class ChatRoomEditForm(ModelForm):
    class Meta:
        model = ChatGroup
        fields = ["groupchat_name"]
        widgets = {
            "groupchat_name": forms.TextInput(
                attrs={
                    "class": "p-4 text-xl font-bold mb-4",
                    "maxlength": "120",
                    "autofocus": True,
                }
            )
        }
