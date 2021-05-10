import abc
from typing import Any, Dict, List

from extractors import ArtifactExtractor, TelegramDesktopArtifactExtractor
from analyzers import ArtifactAnalyzer, TelegramDesktopArtifactAnalyzer
from artifacts.generic import Account, User, Conversation, Message, MessageAttachment
from artifacts.telegram_desktop import TelegramDesktopAccount, TelegramDesktopUser, TelegramDesktopMessage


class InstantMessagingPlatformFactory(metaclass=abc.ABCMeta):
    """Interface that each concrete IM platform factory has to implement."""

    @abc.abstractmethod
    def create_artifact_extractor(self, memory_data_path: str) -> ArtifactExtractor:
        raise NotImplementedError

    @abc.abstractmethod
    def create_artifact_analyzer(self, artifact_extractor: ArtifactExtractor) -> ArtifactAnalyzer:
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

    def create_account(self, dictionary: Dict[str, Any]) -> TelegramDesktopAccount:
        if 'users' in dictionary:
            account: TelegramDesktopAccount = TelegramDesktopAccount(users=dictionary['users'])
            return account

    def create_user(self, dictionary: Dict[str, Any]) -> TelegramDesktopUser:
        if 'name' in dictionary:
            user: TelegramDesktopUser = TelegramDesktopUser(name=dictionary['name'])
            if 'is_contact' in dictionary:
                user.is_contact = dictionary['is_contact']
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
        pass

    def create_message(self, dictionary: Dict[str, Any]) -> TelegramDesktopMessage:
        pass

    def create_message_attachment(self, dictionary: Dict[str, Any]) -> MessageAttachment:
        pass
