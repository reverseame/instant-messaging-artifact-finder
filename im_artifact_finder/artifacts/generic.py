import abc
from datetime import datetime
from typing import List


class Artifact(metaclass=abc.ABCMeta):
    """Interface that all concrete artifacts have to implement."""

    @abc.abstractmethod
    def to_json_format(self) -> str:
        raise NotImplementedError


class MessageAttachment(Artifact, abc.ABC):
    def __init__(self, attachment_id: int):
        self.attachment_id: int = attachment_id


class SharedUser(MessageAttachment, abc.ABC):
    def __init__(self, attachment_id: int, name: str):
        super().__init__(attachment_id)
        self.name: str = name


class File(MessageAttachment, abc.ABC):
    def __init__(self, attachment_id: int, filepath: str, filename: str, filetype: str, size: int):
        super().__init__(attachment_id)
        self.filepath: str = filepath
        self.filename: str = filename
        self.filetype: str = filetype
        self.size: int = size


class GeographicLocation(MessageAttachment, abc.ABC):
    def __init__(self, attachment_id: int, latitude: float, longitude: float):
        super().__init__(attachment_id)
        self.latitude: float = latitude
        self.longitude: float = longitude


class User(Artifact, abc.ABC):
    def __init__(self, user_id: int, name: str, is_contact: bool, is_blocked: bool):
        self.user_id: int = user_id
        self.name: str = name
        self.is_contact: bool = is_contact
        self.is_blocked: bool = is_blocked


class Message(Artifact, abc.ABC):
    def __init__(self, message_id: int, text: str, date: datetime, sender: User, attachments: List[MessageAttachment]):
        self.message_id: int = message_id
        self.text: str = text
        self.date: datetime = date
        self.sender: User = sender
        self.attachments: List[MessageAttachment] = attachments


class Conversation(Artifact, abc.ABC):
    def __init__(self, conversation_id: int, conversation_type: str, name: str, messages: List[Message]):
        self.conversation_id: int = conversation_id
        self.conversation_type: str = conversation_type
        self.name: str = name
        self.messages: List[Message] = messages


class Group(Conversation, abc.ABC):
    def __init__(self, conversation_id: int, conversation_type: str, name: str, messages: List[Message],
                 participants: List[User], admins: List[User]):
        super().__init__(conversation_id, conversation_type, name, messages)
        self.participants: List[User] = participants
        self.admins: List[User] = admins


class Channel(Conversation, abc.ABC):
    def __init__(self, conversation_id: int, conversation_type: str, name: str, messages: List[Message],
                 publishers: List[User], subscribers: List[User]):
        super().__init__(conversation_id, conversation_type, name, messages)
        self.publishers: List[User] = publishers
        self.subscribers: List[User] = subscribers


class IndividualConversation(Conversation, abc.ABC):
    def __init__(self, conversation_id: int, conversation_type: str, name: str, messages: List[Message],
                 users: List[User]):
        super().__init__(conversation_id, conversation_type, name, messages)
        self.users: List[User] = users


class Account(Artifact, abc.ABC):
    def __init__(self, account_id: int, owner: User, users: List[User], conversations: List[Conversation]):
        self.account_id: int = account_id
        self.owner: User = owner
        self.users: List[User] = users
        self.conversations: List[Conversation] = conversations
