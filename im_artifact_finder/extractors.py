import abc
from typing import List


class ArtifactExtractor(metaclass=abc.ABCMeta):
    """Interface that each concrete IM platform artifact extractor has to implement."""

    @abc.abstractmethod
    def extract_accounts(self) -> List[bytes]:
        raise NotImplementedError

    @abc.abstractmethod
    def extract_contacts(self) -> List[bytes]:
        raise NotImplementedError

    @abc.abstractmethod
    def extract_conversations(self) -> List[bytes]:
        raise NotImplementedError

    @abc.abstractmethod
    def extract_messages(self) -> List[bytes]:
        raise NotImplementedError

    @abc.abstractmethod
    def extract_message_attachments(self) -> List[bytes]:
        raise NotImplementedError


class TelegramDesktopArtifactExtractor(ArtifactExtractor):
    def __init__(self, memory_data_path: str):
        self.memory_data_path = memory_data_path

    def extract_accounts(self) -> List[bytes]:
        pass

    def extract_contacts(self) -> List[bytes]:
        pass

    def extract_conversations(self) -> List[bytes]:
        pass

    def extract_messages(self) -> List[bytes]:
        pass

    def extract_message_attachments(self) -> List[bytes]:
        pass

    def extract_qstring(self, virtual_address: str) -> str:
        pass
