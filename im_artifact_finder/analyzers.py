import abc
from typing import Any, Dict

from extractors import TelegramDesktopArtifactExtractor


class ArtifactAnalyzer(metaclass=abc.ABCMeta):
    """Interface that each concrete IM platform artifact analyzer has to implement."""

    @abc.abstractmethod
    def analyze_account(self, data: bytes) -> Dict[str, Any]:
        raise NotImplementedError

    @abc.abstractmethod
    def analyze_contact(self) -> Dict[str, Any]:
        raise NotImplementedError

    @abc.abstractmethod
    def analyze_conversation(self) -> Dict[str, Any]:
        raise NotImplementedError

    @abc.abstractmethod
    def analyze_message(self) -> Dict[str, Any]:
        raise NotImplementedError

    @abc.abstractmethod
    def analyze_message_attachment(self) -> Dict[str, Any]:
        raise NotImplementedError


class TelegramDesktopArtifactAnalyzer(ArtifactAnalyzer):
    def __init__(self, artifact_extractor: TelegramDesktopArtifactExtractor):
        self.artifact_extractor = artifact_extractor

    def analyze_account(self, data: bytes) -> Dict[str, Any]:
        pass

    def analyze_contact(self) -> Dict[str, Any]:
        pass

    def analyze_conversation(self) -> Dict[str, Any]:
        pass

    def analyze_message(self) -> Dict[str, Any]:
        pass

    def analyze_message_attachment(self) -> Dict[str, Any]:
        pass
