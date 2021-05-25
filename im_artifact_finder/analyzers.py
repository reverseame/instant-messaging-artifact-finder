import abc
from typing import Dict, List, Any
import logging
from datetime import datetime, timezone
import struct

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
        self.file_offsets: Dict[str, int] = {'filename': 80, 'filetype': 88}
        self.shared_contact_offsets: Dict[str, int] = {'firstname': 24, 'lastname': 32, 'phone_number': 40}
        self.media_location_offsets: Dict[str, int] = {'latitude': 16, 'longitude': 24, 'title': 48, 'description': 56}

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

        is_bot_offset: int = self.artifact_extractor.user_offsets['is_bot']
        is_bot_data: bytes = raw_data[is_bot_offset: is_bot_offset + 8]
        if is_bot_data != b'\x00\x00\x00\x00\x00\x00\x00\x00':  # If the pointer is not nullptr
            user_data['is_bot'] = True
        else:
            user_data['is_bot'] = False

        is_blocked_offset: int = self.artifact_extractor.user_offsets['is_blocked']
        is_blocked_data: bytes = raw_data[is_blocked_offset: is_blocked_offset + 1]
        if is_blocked_data == b'\x01':
            user_data['is_blocked'] = True
        elif is_blocked_data == b'\x02':
            user_data['is_blocked'] = False

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
        message_offsets: Dict[str, int] = {'history': 8, 'from': 16, 'text': 48, 'media': 120, 'date': 128,
                                           'timetext': 160}
        history_offsets: Dict[str, int] = {'peer': 192}

        # Get the _text QString contents address
        # _text is an attribute that belongs to the class String
        text_contents_address = bytearray(raw_data[message_offsets['text']:message_offsets['text'] + 8])
        text_contents_address_as_str: str = little_endian_to_big_endian(text_contents_address)
        if self.artifact_extractor.is_address_of_qstring_contents(text_contents_address_as_str):
            text: str = self.artifact_extractor.extract_qstring_text(text_contents_address_as_str)
            if text is not None and text.endswith('_'):
                text = text[:-1]
            message_data['text'] = text

        # Get _date contents
        # _date is an attribute that belongs to the class HistoryItem
        # _date represents the moment when the sender sent the message
        # _date is stored as seconds since 1 January 1970
        epoch_date = bytearray(raw_data[message_offsets['date']:message_offsets['date'] + 4])
        epoch_date_as_int: int = int(little_endian_to_big_endian(epoch_date), 16)
        message_data['date'] = datetime.fromtimestamp(epoch_date_as_int, timezone.utc)

        # Get _from pointer, in order to identify the sender of the message
        from_pointer = bytearray(raw_data[message_offsets['from']:message_offsets['from'] + 8])
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
        history_pointer = bytearray(raw_data[message_offsets['history']:message_offsets['history'] + 8])
        history_pointer_as_str: str = little_endian_to_big_endian(history_pointer)
        history_raw_data: bytes = extract_surroundings(self.artifact_extractor.memory_data_path, history_pointer_as_str,
                                                       0, history_offsets['peer'] + 8)
        if history_raw_data is not None:
            # Get the peer attribute from the History object
            peerdata_address = bytearray(
                history_raw_data[history_offsets['peer']:history_offsets['peer'] + 8])
            peerdata_address_as_str: str = little_endian_to_big_endian(peerdata_address)
            if self.is_peerdata_address(peerdata_address_as_str):
                raw_peerdata: bytes = extract_surroundings(self.artifact_extractor.memory_data_path,
                                                           peerdata_address_as_str, 0, 24)
                if raw_peerdata is not None:
                    message_data['conversation'] = self.analyze_conversation(raw_peerdata)

        # Check if the message has an attachment (the attachments are subclasses of Media)
        media_pointer: bytes = raw_data[message_offsets['media']:message_offsets['media'] + 8]
        if media_pointer != b'\x00\x00\x00\x00\x00\x00\x00\x00':
            # Get the Media object
            media_pointer_as_str: str = little_endian_to_big_endian(bytearray(media_pointer))
            raw_media: bytes = extract_surroundings(self.artifact_extractor.memory_data_path,
                                                    media_pointer_as_str, 0, 64)
            # Analyze the Media object
            if raw_media is not None:
                message_attachment_data: Dict[str, Any] = self.analyze_message_attachment(raw_media)
                if 'attachment_type' in message_attachment_data:
                    message_data['attachment'] = message_attachment_data

        return message_data

    def analyze_message_attachment(self, raw_data: bytes) -> Dict[str, Any]:
        message_attachment_data: Dict[str, Any] = {}
        media_file_offsets: Dict[str, int] = {'document': 16}

        # Check if the attachment is a file (represented with the MediaFile and DocumentData classes)
        # Get the pointer to a DocumentData object. That pointer is stored in a MediaFile object
        documentdata_subpattern_size: int = 6 * 16
        documentdata_address: bytes = raw_data[
                                      media_file_offsets['document']: media_file_offsets['document'] + 8]
        documentdata_address_as_str: str = little_endian_to_big_endian(bytearray(documentdata_address))
        if self.is_documentdata_address(documentdata_address_as_str):

            raw_documentdata: bytes = extract_surroundings(self.artifact_extractor.memory_data_path,
                                                           documentdata_address_as_str, 0, documentdata_subpattern_size)

            if raw_documentdata is not None:
                # Get the name of the file
                filename_contents_address = bytearray(
                    raw_documentdata[self.file_offsets['filename']:self.file_offsets['filename'] + 8])
                filename_contents_address_as_str: str = little_endian_to_big_endian(filename_contents_address)
                filename_text = self.artifact_extractor.extract_qstring_text(filename_contents_address_as_str)
                if filename_text is not None and filename_text != '' and bytes(filename_text, 'utf-8') != b'\x00':
                    message_attachment_data['filename'] = filename_text

                # Get the type of the file
                filetype_contents_address = bytearray(
                    raw_documentdata[self.file_offsets['filetype']:self.file_offsets['filetype'] + 8])
                filetype_contents_address_as_str: str = little_endian_to_big_endian(filetype_contents_address)
                filetype_text = self.artifact_extractor.extract_qstring_text(filetype_contents_address_as_str)
                if filetype_text is not None and filetype_text != '' and bytes(filetype_text, 'utf-8') != b'\x00':
                    message_attachment_data['filetype'] = filetype_text

                if 'filename' in message_attachment_data and 'filetype' in message_attachment_data:
                    message_attachment_data['attachment_type'] = 'file'

        # Check if the attachment is a shared contact (represented with the MediaContact and SharedContact classes)
        if self.is_media_contact(raw_data):
            # Get the contact first name
            firstname_contents_address = bytearray(
                raw_data[self.shared_contact_offsets['firstname']:self.shared_contact_offsets['firstname'] + 8])
            firstname_contents_address_as_str: str = little_endian_to_big_endian(firstname_contents_address)
            firstname_text = self.artifact_extractor.extract_qstring_text(firstname_contents_address_as_str)
            if firstname_text is not None and firstname_text != '' and bytes(firstname_text, 'utf-8') != b'\x00':
                message_attachment_data['firstname'] = firstname_text

            # Get the contact last name
            lastname_contents_address = bytearray(
                raw_data[self.shared_contact_offsets['lastname']:self.shared_contact_offsets['lastname'] + 8])
            lastname_contents_address_as_str: str = little_endian_to_big_endian(lastname_contents_address)
            lastname_text = self.artifact_extractor.extract_qstring_text(lastname_contents_address_as_str)
            if lastname_text is not None and lastname_text != '' and bytes(lastname_text, 'utf-8') != b'\x00':
                message_attachment_data['lastname'] = lastname_text

            # Get the contact phone number
            phone_number_contents_address = bytearray(
                raw_data[self.shared_contact_offsets['phone_number']:self.shared_contact_offsets['phone_number'] + 8])
            phone_number_contents_address_as_str: str = little_endian_to_big_endian(phone_number_contents_address)
            phone_number_text = self.artifact_extractor.extract_qstring_text(phone_number_contents_address_as_str)
            if phone_number_text is not None and phone_number_text != '' and bytes(phone_number_text,
                                                                                   'utf-8') != b'\x00':
                message_attachment_data['phone_number'] = phone_number_text

            if 'firstname' in message_attachment_data:
                message_attachment_data['attachment_type'] = 'shared_contact'

        # Check if the attachment is a geographic location (represented with the MediaLocation and LocationPoint classes)
        if self.is_media_location(raw_data):
            # Get the latitude
            latitude = bytearray(
                raw_data[self.media_location_offsets['latitude']:self.media_location_offsets['latitude'] + 8])
            latitude_as_float: int = struct.unpack('!d', bytes.fromhex(little_endian_to_big_endian(latitude)))[0]
            message_attachment_data['latitude'] = latitude_as_float

            # Get the longitude
            longitude = bytearray(
                raw_data[self.media_location_offsets['longitude']:self.media_location_offsets['longitude'] + 8])
            longitude_as_float: float = struct.unpack('!d', bytes.fromhex(little_endian_to_big_endian(longitude)))[0]
            message_attachment_data['longitude'] = longitude_as_float

            # Get the geographic location title
            title_contents_address = bytearray(
                raw_data[self.media_location_offsets['title']:self.media_location_offsets['title'] + 8])
            title_contents_address_as_str: str = little_endian_to_big_endian(title_contents_address)
            title_text = self.artifact_extractor.extract_qstring_text(title_contents_address_as_str)
            if title_text is not None and title_text != '' and bytes(title_text, 'utf-8') != b'\x00':
                message_attachment_data['title'] = title_text

            # Get the geographic location description
            description_contents_address = bytearray(
                raw_data[self.media_location_offsets['description']:
                         self.media_location_offsets['description'] + 8])
            description_contents_address_as_str: str = little_endian_to_big_endian(description_contents_address)
            description_text = self.artifact_extractor.extract_qstring_text(description_contents_address_as_str)
            if description_text is not None and description_text != '' and bytes(description_text, 'utf-8') != b'\x00':
                message_attachment_data['description'] = description_text

            if 'latitude' in message_attachment_data and 'longitude' in message_attachment_data:
                message_attachment_data['attachment_type'] = 'geographic_location'

        return message_attachment_data

    def is_peerdata_address(self, address: str) -> bool:
        """Find out if the given address corresponds to the beginning of a PeerData object"""
        raw_peerdata: bytes = extract_surroundings(self.artifact_extractor.memory_data_path, address, 0, 24)
        if raw_peerdata is not None:
            name_contents_address: str = little_endian_to_big_endian(bytearray(raw_peerdata[16:24]))
            if self.artifact_extractor.is_address_of_qstring_contents(name_contents_address):
                return True
        return False

    def is_documentdata_address(self, address: str) -> bool:
        """Find out if the given address corresponds to the beginning of a DocumentData object"""
        address_as_int = int(address, 16)
        qstring_offsets: List[int] = [self.file_offsets['filename'], self.file_offsets['filetype']]

        for qstring_offset in qstring_offsets:
            # Obtain the address in little endian
            qstring_contents_address: bytes = extract_surroundings(self.artifact_extractor.memory_data_path,
                                                                   hex(address_as_int + qstring_offset), 0, 8)
            if qstring_contents_address is not None:
                if not self.artifact_extractor.is_address_of_qstring_contents(
                        little_endian_to_big_endian(bytearray(qstring_contents_address))):
                    return False
            else:
                return False

        return True

    def is_media_contact(self, raw_contact: bytes) -> bool:
        """Check if the given data is a MediaContact object"""
        qstring_offsets: List[int] = [self.shared_contact_offsets['firstname'], self.shared_contact_offsets['lastname'],
                                      self.shared_contact_offsets['phone_number']]

        for qstring_offset in qstring_offsets:
            qstring_contents_address: bytes = raw_contact[qstring_offset: qstring_offset + 8]
            if not self.artifact_extractor.is_address_of_qstring_contents(
                    little_endian_to_big_endian(bytearray(qstring_contents_address))):
                return False

        return True

    def is_media_location(self, raw_location: bytes) -> bool:
        """Check if the given data is a MediaLocation object"""
        qstring_offsets: List[int] = [self.media_location_offsets['title'],
                                      self.media_location_offsets['description']]

        for qstring_offset in qstring_offsets:
            qstring_contents_address: bytes = raw_location[qstring_offset: qstring_offset + 8]
            if not self.artifact_extractor.is_address_of_qstring_contents(
                    little_endian_to_big_endian(bytearray(qstring_contents_address))):
                return False

        return True


def little_endian_to_big_endian(data_as_bytearray: bytearray) -> str:
    """Transform data from little endian to big endian"""
    data_as_bytearray.reverse()
    return bytes(data_as_bytearray).hex()
