import abc
from typing import Any, Dict, List
import logging

from extractors import ArtifactExtractor, TelegramDesktopArtifactExtractor
from analyzers import ArtifactAnalyzer, TelegramDesktopArtifactAnalyzer
from organizers import ArtifactOrganizer, TelegramDesktopArtifactOrganizer, is_user_repeated
from artifacts.generic import Account, User, Conversation, Message, MessageAttachment
from artifacts.telegram_desktop import TelegramDesktopAccount, TelegramDesktopUser, TelegramDesktopMessage, \
    TelegramDesktopIndividualConversation, TelegramDesktopGroup, TelegramDesktopChannel

logger = logging.getLogger(__name__)


class InstantMessagingPlatformFactory(metaclass=abc.ABCMeta):
    """Interface that each concrete IM platform factory has to implement."""

    @abc.abstractmethod
    def create_artifact_extractor(self, memory_data_path: str) -> ArtifactExtractor:
        raise NotImplementedError

    @abc.abstractmethod
    def create_artifact_analyzer(self, artifact_extractor: ArtifactExtractor) -> ArtifactAnalyzer:
        raise NotImplementedError

    @abc.abstractmethod
    def create_artifact_organizer(self) -> ArtifactOrganizer:
        raise NotImplementedError

    @abc.abstractmethod
    def create_account(self, dictionary: Dict[str, Any]) -> Account:
        raise NotImplementedError

    @abc.abstractmethod
    def create_user(self, dictionary: Dict[str, Any]) -> User:
        raise NotImplementedError

    @abc.abstractmethod
    def create_conversation(self, dictionary: Dict[str, Any]) -> Conversation:
        raise NotImplementedError

    @abc.abstractmethod
    def create_message(self, dictionary: Dict[str, Any]) -> Message:
        raise NotImplementedError

    @abc.abstractmethod
    def create_message_attachment(self, dictionary: Dict[str, Any]) -> MessageAttachment:
        raise NotImplementedError


class TelegramDesktopFactory(InstantMessagingPlatformFactory):
    def create_artifact_extractor(self, memory_data_path: str) -> TelegramDesktopArtifactExtractor:
        return TelegramDesktopArtifactExtractor(memory_data_path)

    def create_artifact_analyzer(self,
                                 artifact_extractor: TelegramDesktopArtifactExtractor) -> TelegramDesktopArtifactAnalyzer:
        return TelegramDesktopArtifactAnalyzer(artifact_extractor)

    def create_artifact_organizer(self) -> TelegramDesktopArtifactOrganizer:
        return TelegramDesktopArtifactOrganizer()

    def create_account(self, dictionary: Dict[str, Any]) -> TelegramDesktopAccount:
        if 'users' in dictionary:
            users: List[User] = []
            for user_data in dictionary['users']:
                user: TelegramDesktopUser = self.create_user(user_data)
                if user is not None:
                    users.append(user)
            account: TelegramDesktopAccount = TelegramDesktopAccount()
            if 'owner' in dictionary:
                owner: TelegramDesktopUser = self.create_user(dictionary['owner'])
                if owner is not None:
                    account.owner = owner
            if 'conversations' in dictionary:
                conversations: List[Conversation] = []
                for conversation_data in dictionary['conversations']:
                    conversation: Conversation = self.create_conversation(conversation_data)
                    if conversation is not None:
                        conversations.append(conversation)
                account.conversations = conversations
                logger.info(f'Number of Telegram Desktop conversations retrieved: {len(conversations)}')
                message_counter: int = 0
                for conversation in conversations:
                    message_counter += len(conversation.messages)
                    for message in conversation.messages:
                        if not is_user_repeated(users, message.sender):
                            users.append(message.sender)
                account.users = users
                logger.info(f'Number of Telegram Desktop messages retrieved: {message_counter}')
                logger.info(f'Number of Telegram Desktop users retrieved: {len(users)}')

            return account

    def create_user(self, dictionary: Dict[str, Any]) -> TelegramDesktopUser:
        if 'name' in dictionary:
            user: TelegramDesktopUser = TelegramDesktopUser(name=dictionary['name'])
            if 'is_contact' in dictionary:
                user.is_contact = dictionary['is_contact']
            if 'id' in dictionary:
                user.user_id = dictionary['id']
            if 'is_bot' in dictionary:
                user.is_bot = dictionary['is_bot']
            if 'is_blocked' in dictionary:
                user.is_blocked = dictionary['is_blocked']
            if 'strings' in dictionary:
                strings: List[str] = dictionary['strings']
                if len(strings) >= 2 and strings[0] + ' ' + strings[1] == dictionary['name']:
                    strings.pop(0)
                    strings.pop(0)
                elif len(strings) >= 1 and strings[0] == dictionary['name']:
                    strings.pop(0)
                if len(strings) == 2:
                    user.username = strings[0]
                    user.phone_number = strings[1]
                elif len(strings) == 1:
                    if strings[0].isdigit():
                        user.phone_number = strings[0]
                    else:
                        user.username = strings[0]
            return user

    def create_conversation(self, dictionary: Dict[str, Any]) -> Conversation:
        if 'type' in dictionary:
            conversation_type: str = dictionary['type']
            conversation = None
            if conversation_type == 'Individual conversation':
                conversation = TelegramDesktopIndividualConversation()
            elif conversation_type == 'Group':
                conversation = TelegramDesktopGroup()
            elif conversation_type == 'Channel':
                conversation = TelegramDesktopChannel()
            if conversation is not None:
                if 'id' in dictionary:
                    conversation.conversation_id = dictionary['id']
                if 'name' in dictionary:
                    conversation.name = dictionary['name']
                if 'messages' in dictionary:
                    messages: List[TelegramDesktopMessage] = []
                    for message_data in dictionary['messages']:
                        message: TelegramDesktopMessage = self.create_message(message_data)
                        if message is not None:
                            messages.append(message)
                    messages.sort(key=lambda x: x.date)  # Sort the messages by the time they were sent
                    conversation.messages = messages
                    # If the conversation is an individual conversation, identify the two users involved
                    if conversation_type == 'Individual conversation':
                        users: List[User] = []
                        for message in messages:
                            if message.sender is not None and not is_user_repeated(users, message.sender):
                                users.append(message.sender)
                        conversation.users = users
            return conversation

    def create_message(self, dictionary: Dict[str, Any]) -> TelegramDesktopMessage:
        if 'text' in dictionary:
            message: TelegramDesktopMessage = TelegramDesktopMessage(text=dictionary['text'])
            if 'date' in dictionary:
                message.date = dictionary['date']
            if 'sender' in dictionary:
                if 'strings' in dictionary['sender']:
                    sender: TelegramDesktopUser = self.create_user(dictionary['sender'])
                    if sender is not None:
                        message.sender = sender
                else:
                    message.sender = TelegramDesktopUser(user_id=dictionary['sender']['id'],
                                                         name=dictionary['sender']['name'])
            return message

    def create_message_attachment(self, dictionary: Dict[str, Any]) -> MessageAttachment:
        pass
