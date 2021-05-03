import json
from typing import List
from datetime import datetime

from .utils import dictionary_representation
from .generic import File, GeographicLocation, User, Message, MessageAttachment, Group, Channel, IndividualConversation, \
    Account, Conversation


class TelegramDesktopFile(File):
    def __init__(self, attachment_id: int, filepath: str, filename: str, size: int, url: str):
        super().__init__(attachment_id, filepath, filename)
        self.size: int = size
        self.url: str = url

    def to_json_format(self) -> str:
        return json.dumps(self, ensure_ascii=False, indent=4, default=dictionary_representation)


class TelegramDesktopGeographicLocation(GeographicLocation):
    def __init__(self, attachment_id: int, longitude: float, latitude: float, title: str, description: str):
        super().__init__(attachment_id, longitude, latitude)
        self.title: str = title
        self.description: str = description

    def to_json_format(self) -> str:
        return json.dumps(self, ensure_ascii=False, indent=4, default=dictionary_representation)


class TelegramDesktopUser(User):
    def __init__(self, user_id: int, name: str, is_contact: bool, is_blocked: bool, phone_number: int, username: str,
                 about: str, is_bot: bool):
        super().__init__(user_id, name, is_contact, is_blocked)
        self.phone_number: int = phone_number
        self.username: str = username
        self.about: str = about
        self.is_bot: bool = is_bot

    def to_json_format(self) -> str:
        return json.dumps(self, ensure_ascii=False, indent=4, default=dictionary_representation)


class TelegramDesktopMessage(Message):
    def __init__(self, message_id: int, text: str, date: datetime, sender: TelegramDesktopUser,
                 attachments: List[MessageAttachment]):
        super().__init__(message_id, text, date, sender, attachments)

    def to_json_format(self) -> str:
        return json.dumps(self, ensure_ascii=False, indent=4, default=dictionary_representation)


class TelegramDesktopGroup(Group):
    def __init__(self, conversation_id: int, name: str, messages: List[TelegramDesktopMessage],
                 participants: List[TelegramDesktopUser], admins: List[TelegramDesktopUser], participants_count: int,
                 admins_count: int, is_megagroup: bool, is_public: bool, creator: TelegramDesktopUser):
        super().__init__(conversation_id, name, messages, participants, admins)
        self.participants_count: int = participants_count
        self.admins_count: int = admins_count
        self.is_megagroup: bool = is_megagroup
        self.is_public: bool = is_public
        self.creator: TelegramDesktopUser = creator

    def to_json_format(self) -> str:
        return json.dumps(self, ensure_ascii=False, indent=4, default=dictionary_representation)


class TelegramDesktopChannel(Channel):
    def __init__(self, conversation_id: int, name: str, messages: List[TelegramDesktopMessage],
                 publishers: List[TelegramDesktopUser], subscribers: List[TelegramDesktopUser], subscribers_count: int,
                 publishers_count: int, is_public: bool):
        super().__init__(conversation_id, name, messages, publishers, subscribers)
        self.subscribers_count: int = subscribers_count
        self.publishers_count: int = publishers_count
        self.is_public: bool = is_public

    def to_json_format(self) -> str:
        return json.dumps(self, ensure_ascii=False, indent=4, default=dictionary_representation)


class TelegramDesktopIndividualConversation(IndividualConversation):
    def __init__(self, conversation_id: int, name: str, messages: List[TelegramDesktopMessage],
                 users: List[TelegramDesktopUser]):
        super().__init__(conversation_id, name, messages, users)

    def to_json_format(self) -> str:
        return json.dumps(self, ensure_ascii=False, indent=4, default=dictionary_representation)


class TelegramDesktopAccount(Account):
    def __init__(self, account_id: int, user: TelegramDesktopUser, contacts: List[TelegramDesktopUser],
                 conversations: List[Conversation]):
        super().__init__(account_id, user, contacts, conversations)

    def to_json_format(self) -> str:
        return json.dumps(self, ensure_ascii=False, indent=4, default=dictionary_representation)
