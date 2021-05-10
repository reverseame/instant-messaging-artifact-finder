import abc
from typing import Dict, List, Any

from extractors import TelegramDesktopArtifactExtractor


class ArtifactAnalyzer(metaclass=abc.ABCMeta):
    """Interface that each concrete IM platform artifact analyzer has to implement."""

    @abc.abstractmethod
    def analyze_account(self, raw_data: bytes) -> Dict[str, Any]:
        raise NotImplementedError

    @abc.abstractmethod
    def analyze_user(self, raw_data: bytes) -> Dict[str, Any]:
        raise NotImplementedError

    @abc.abstractmethod
    def analyze_conversation(self, raw_data: bytes) -> Dict[str, Any]:
        raise NotImplementedError

    @abc.abstractmethod
    def analyze_message(self, raw_data: bytes) -> Dict[str, Any]:
        raise NotImplementedError

    @abc.abstractmethod
    def analyze_message_attachment(self, raw_data: bytes) -> Dict[str, Any]:
        raise NotImplementedError


class TelegramDesktopArtifactAnalyzer(ArtifactAnalyzer):
    def __init__(self, artifact_extractor: TelegramDesktopArtifactExtractor):
        self.artifact_extractor = artifact_extractor

    def analyze_account(self, raw_data: bytes) -> Dict[str, Any]:
        pass

    def analyze_user(self, raw_data: bytes) -> Dict[str, Any]:
        user_strings: List[str] = []  # List that stores information about the user
        # Obtain, in order, each 64 bit word, which will be in little endian
        for i in range(0, len(raw_data), 8):
            word_as_bytearray = bytearray(raw_data[i:i + 8])
            # Transform the word to big endian
            word_as_bytearray.reverse()
            word_as_str: str = bytes(word_as_bytearray).hex()
            # Check if the word is an address that points to the contents of a QString object
            if self.artifact_extractor.is_address_of_qstring_contents(word_as_str):
                qstring_text = self.artifact_extractor.extract_qstring_text(word_as_str)
                if qstring_text is not None and qstring_text != '' and bytes(qstring_text, 'utf-8') != b'\x00':
                    user_strings.append(qstring_text)

        name: str = user_strings.pop(0)  # Full name of the user
        user_data: Dict[str, Any] = {'name': name, 'strings': user_strings}
        is_contact_offset: int = self.artifact_extractor.user_offsets['is_contact']
        is_contact_data: bytes = raw_data[is_contact_offset: is_contact_offset + 1]
        if is_contact_data == b'\x01':
            user_data['is_contact'] = True
        elif is_contact_data == b'\x02':
            user_data['is_contact'] = False
        return user_data

    def analyze_conversation(self, raw_data: bytes) -> Dict[str, Any]:
        pass

    def analyze_message(self, raw_data: bytes) -> Dict[str, Any]:
        pass

    def analyze_message_attachment(self, raw_data: bytes) -> Dict[str, Any]:
        pass
