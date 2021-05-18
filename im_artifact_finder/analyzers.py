import abc
from typing import Dict, List, Any
import logging
from datetime import datetime, timezone

from extractors import TelegramDesktopArtifactExtractor, extract_surroundings

logger = logging.getLogger(__name__)


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
        self.message_offsets: Dict[str, int] = {'history': 8, 'from': 16, 'text': 48, 'date': 128, 'timetext': 160}
        self.history_offsets: Dict[str, int] = {'peer': 192}

    def analyze_account(self, raw_data: bytes) -> Dict[str, Any]:
        return {}

    def analyze_user(self, raw_data: bytes) -> Dict[str, Any]:
        user_strings: List[str] = []  # List that stores information about the user
        qstring_offsets: List[int] = [self.artifact_extractor.user_offsets['name'],
                                      self.artifact_extractor.user_offsets['firstname'],
                                      self.artifact_extractor.user_offsets['lastname'],
                                      self.artifact_extractor.user_offsets['username'],
                                      self.artifact_extractor.user_offsets['phone']]
        # Obtain each QString contents address, which will be in little endian
        for qstring_offset in qstring_offsets:
            qstring_contents_address = bytearray(raw_data[qstring_offset:qstring_offset + 8])
            # Transform the address to big endian
            qstring_contents_address_as_str: str = little_endian_to_big_endian(qstring_contents_address)
            # Check if the address points to the contents of a QString object
            if self.artifact_extractor.is_address_of_qstring_contents(qstring_contents_address_as_str):
                qstring_text = self.artifact_extractor.extract_qstring_text(qstring_contents_address_as_str)
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
        user_id_offset: int = self.artifact_extractor.user_offsets['id']
        user_id_data: int = int(little_endian_to_big_endian(bytearray(raw_data[user_id_offset:user_id_offset + 8])), 16)
        user_data['id'] = user_id_data
        return user_data

    def analyze_conversation(self, raw_data: bytes) -> Dict[str, Any]:
        conversation_data: Dict[str, Any] = {}
        name_contents_address: str = little_endian_to_big_endian(bytearray(raw_data[16:24]))
        name_text = self.artifact_extractor.extract_qstring_text(name_contents_address)
        if name_text is not None and name_text != '' and bytes(name_text, 'utf-8') != b'\x00':
            conversation_data['name'] = name_text

        peer_id_type_mask: int = 0xF00000000
        peer_id_user_shift: int = 0x000000000
        peer_id_chat_shift: int = 0x100000000
        peer_id_channel_shift: int = 0x200000000
        peer_id: int = int(little_endian_to_big_endian(bytearray(raw_data[8:16])), 16)
        conversation_data['id'] = peer_id
        if peer_id & peer_id_type_mask == peer_id_user_shift:
            conversation_data['type'] = 'Individual conversation'
        elif peer_id & peer_id_type_mask == peer_id_chat_shift:
            conversation_data['type'] = 'Group'
        elif peer_id & peer_id_type_mask == peer_id_channel_shift:
            conversation_data['type'] = 'Channel'
        else:
            conversation_data['type'] = 'Unknown'
        return conversation_data

    def analyze_message(self, raw_data: bytes) -> Dict[str, Any]:
        message_data: Dict[str, Any] = {}

        # Get the _text QString contents address
        # _text is an attribute that belongs to the class String
        text_contents_address = bytearray(raw_data[self.message_offsets['text']:self.message_offsets['text'] + 8])
        text_contents_address_as_str: str = little_endian_to_big_endian(text_contents_address)
        if self.artifact_extractor.is_address_of_qstring_contents(text_contents_address_as_str):
            text: str = self.artifact_extractor.extract_qstring_text(text_contents_address_as_str)
            if text.endswith('_'):
                text = text[:-1]
            message_data['text'] = text

        # Get _date contents
        # _date is an attribute that belongs to the class HistoryItem
        # _date represents the moment when the sender sent the message
        # _date is stored as seconds since 1 January 1970
        epoch_date = bytearray(raw_data[self.message_offsets['date']:self.message_offsets['date'] + 4])
        epoch_date_as_int: int = int(little_endian_to_big_endian(epoch_date), 16)
        message_data['date'] = datetime.fromtimestamp(epoch_date_as_int, timezone.utc)

        # Get _from pointer, in order to identify the sender of the message
        from_pointer = bytearray(raw_data[self.message_offsets['from']:self.message_offsets['from'] + 8])
        from_pointer_as_str: str = little_endian_to_big_endian(from_pointer)
        if self.artifact_extractor.is_raw_user(from_pointer_as_str):
            raw_from_userdata: bytes = extract_surroundings(self.artifact_extractor.memory_data_path,
                                                            from_pointer_as_str, 0,
                                                            self.artifact_extractor.user_subpattern_size)
            if raw_from_userdata is not None:
                message_data['sender'] = self.analyze_user(raw_from_userdata)
        elif self.is_peerdata_address(from_pointer_as_str):
            raw_from_peerdata: bytes = extract_surroundings(self.artifact_extractor.memory_data_path,
                                                            from_pointer_as_str, 0, 24)
            if raw_from_peerdata is not None:
                message_data['sender'] = self.analyze_conversation(raw_from_peerdata)

        # Get _history pointer, in order to identify the conversation where the message was sent
        history_pointer = bytearray(raw_data[self.message_offsets['history']:self.message_offsets['history'] + 8])
        history_pointer_as_str: str = little_endian_to_big_endian(history_pointer)
        history_raw_data: bytes = extract_surroundings(self.artifact_extractor.memory_data_path, history_pointer_as_str,
                                                       0, self.history_offsets['peer'] + 8)
        if history_raw_data is not None:
            # Get the peer attribute from the History object
            peerdata_address = bytearray(
                history_raw_data[self.history_offsets['peer']:self.history_offsets['peer'] + 8])
            peerdata_address_as_str: str = little_endian_to_big_endian(peerdata_address)
            if self.is_peerdata_address(peerdata_address_as_str):
                raw_peerdata: bytes = extract_surroundings(self.artifact_extractor.memory_data_path,
                                                           peerdata_address_as_str, 0, 24)
                if raw_peerdata is not None:
                    message_data['conversation'] = self.analyze_conversation(raw_peerdata)

        return message_data

    def analyze_message_attachment(self, raw_data: bytes) -> Dict[str, Any]:
        return {}

    def is_peerdata_address(self, address: str) -> bool:
        """Find out if the given address corresponds to the beginning of a PeerData object"""
        raw_peerdata: bytes = extract_surroundings(self.artifact_extractor.memory_data_path, address, 0, 24)
        if raw_peerdata is not None:
            name_contents_address: str = little_endian_to_big_endian(bytearray(raw_peerdata[16:24]))
            if self.artifact_extractor.is_address_of_qstring_contents(name_contents_address):
                return True
        return False


def little_endian_to_big_endian(data_as_bytearray: bytearray) -> str:
    """Transform data from little endian to big endian"""
    data_as_bytearray.reverse()
    return bytes(data_as_bytearray).hex()
