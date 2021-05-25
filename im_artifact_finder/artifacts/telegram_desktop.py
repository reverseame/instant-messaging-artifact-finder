from typing import List
from datetime import datetime

from .utils import json_representation
from .generic import SharedUser, File, GeographicLocation, User, Message, MessageAttachment, Group, Channel, \
    IndividualConversation, Account, Conversation


class TelegramDesktopSharedUser(SharedUser):
    def __init__(self, attachment_id: int = None, name: str = None, phone_number: str = None):
        super().__init__(attachment_id, name)
        self.phone_number: str = phone_number

    def to_json_format(self) -> str:
        return json_representation(self)


class TelegramDesktopFile(File):
    def __init__(self, attachment_id: int = None, filepath: str = None, filename: str = None, filetype: str = None,
                 size: int = None, url: str = None):
        super().__init__(attachment_id, filepath, filename, filetype, size)
        self.url: str = url

    def to_json_format(self) -> str:
        return json_representation(self)


class TelegramDesktopGeographicLocation(GeographicLocation):
    def __init__(self, attachment_id: int = None, latitude: float = None, longitude: float = None, title: str = None,
                 description: str = None):
        super().__init__(attachment_id, latitude, longitude)
        self.title: str = title
        self.description: str = description

    def to_json_format(self) -> str:
        return json_representation(self)


class TelegramDesktopUser(User):
    def __init__(self, user_id: int = None, name: str = None, is_contact: bool = None, is_blocked: bool = None,
                 phone_number: int = None, username: str = None, about: str = None, is_bot: bool = None):
        super().__init__(user_id, name, is_contact, is_blocked)
        self.phone_number: int = phone_number
        self.username: str = username
        self.about: str = about
        self.is_bot: bool = is_bot

    def to_json_format(self) -> str:
        return json_representation(self)


class TelegramDesktopMessage(Message):
    def __init__(self, message_id: int = None, text: str = None, date: datetime = None,
                 sender: TelegramDesktopUser = None, attachments: List[MessageAttachment] = None):
        super().__init__(message_id, text, date, sender, attachments)

    def to_json_format(self) -> str:
        return json_representation(self)


class TelegramDesktopGroup(Group):
    def __init__(self, conversation_id: int = None, conversation_type: str = 'Group', name: str = None,
                 messages: List[TelegramDesktopMessage] = None, participants: List[TelegramDesktopUser] = None,
                 admins: List[TelegramDesktopUser] = None, participants_count: int = None, admins_count: int = None,
                 is_megagroup: bool = None, is_public: bool = None, creator: TelegramDesktopUser = None):
        super().__init__(conversation_id, conversation_type, name, messages, participants, admins)
        self.participants_count: int = participants_count
        self.admins_count: int = admins_count
        self.is_megagroup: bool = is_megagroup
        self.is_public: bool = is_public
        self.creator: TelegramDesktopUser = creator

    def to_json_format(self) -> str:
        return json_representation(self)


class TelegramDesktopChannel(Channel):
    def __init__(self, conversation_id: int = None, conversation_type: str = 'Channel', name: str = None,
                 messages: List[TelegramDesktopMessage] = None, publishers: List[TelegramDesktopUser] = None,
                 subscribers: List[TelegramDesktopUser] = None, subscribers_count: int = None,
                 publishers_count: int = None, is_public: bool = None):
        super().__init__(conversation_id, conversation_type, name, messages, publishers, subscribers)
        self.subscribers_count: int = subscribers_count
        self.publishers_count: int = publishers_count
        self.is_public: bool = is_public

    def to_json_format(self) -> str:
        return json_representation(self)


class TelegramDesktopIndividualConversation(IndividualConversation):
    def __init__(self, conversation_id: int = None, conversation_type: str = 'Individual conversation',
                 name: str = None, messages: List[TelegramDesktopMessage] = None,
                 users: List[TelegramDesktopUser] = None):
        super().__init__(conversation_id, conversation_type, name, messages, users)

    def to_json_format(self) -> str:
        return json_representation(self)


class TelegramDesktopAccount(Account):
    def __init__(self, account_id: int = None, owner: TelegramDesktopUser = None,
                 users: List[TelegramDesktopUser] = None, conversations: List[Conversation] = None):
        super().__init__(account_id, owner, users, conversations)

    def to_json_format(self) -> str:
        return json_representation(self)
