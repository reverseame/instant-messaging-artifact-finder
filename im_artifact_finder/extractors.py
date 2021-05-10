import abc
from typing import List, Tuple, Dict
import re
import mmap
import os
import struct


class ArtifactExtractor(metaclass=abc.ABCMeta):
    """Interface that each concrete IM platform artifact extractor has to implement."""

    @abc.abstractmethod
    def extract_accounts(self) -> List[bytes]:
        raise NotImplementedError

    @abc.abstractmethod
    def extract_users(self) -> List[bytes]:
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
        self.user_offsets: Dict[str, int] = {'name': 0, 'firstname': 192, 'lastname': 200, 'username': 208,
                                             'phone': 368, 'is_contact': 376}
        # Patterns to find the contents of QString objects
        self.qstring_contents_patterns = {'more_strict': re.compile(
            rb'[\x00\x01\x02][\x00]{3}[\x00-\xff][\x00]{3}[\x00-\xff][\x00]{2}[\x00\x80][\x00-\xff]{4}\x18[\x00]{7}[\x00-\xff]*?[\x00]{2}'),
            'less_strict': re.compile(rb'[\x00-\xff]{16}\x18[\x00]{7}[\x00-\xff]*?[\x00]{2}')}

    def extract_accounts(self) -> List[bytes]:
        pass

    def extract_users(self) -> List[bytes]:
        raw_users: List[bytes] = []
        bytes_above_phone: int = 23 * 16
        bytes_below_phone: int = 16
        user_subpattern_size: int = bytes_above_phone + bytes_below_phone
        # Distance, in bytes, between the same attribute of two users stored next to each other in memory
        distance_between_users: int = 592

        # First, find users based on mobile phone numbers
        phone_number_pattern = re.compile(rb'(\d\x00){7,16}[\x00]{2}')
        phone_numbers: List[Tuple[bytes, str]] = find_matches_and_their_addresses(self.memory_data_path,
                                                                                  phone_number_pattern)
        name_addresses: List[int] = []  # Memory addresses where users full names are stored as QStrings
        for phone_number in phone_numbers:
            # Calculate the address where the contents of the QString object are
            qstring_contents_address: str = hex(int(phone_number[1], 16) - 24)
            if self.is_address_of_qstring_contents(qstring_contents_address):
                qstring_contents_address_as_int: int = int(qstring_contents_address, 16)
                qstring_contents_address_little_endian: bytes = struct.pack('<Q', qstring_contents_address_as_int)
                # Find the QString contents address in memory, and where that address is stored
                matches: List[Tuple[bytes, str]] = find_matches_and_their_addresses(self.memory_data_path,
                                                                                    re.compile(
                                                                                        re.escape(
                                                                                            qstring_contents_address_little_endian)))
                for match in matches:
                    # Around the phone number QString, additional information about a user can be found
                    contents: bytes = extract_surroundings(self.memory_data_path, match[1], bytes_above_phone,
                                                           bytes_below_phone)
                    name_address: int = int(match[1], 16) - bytes_above_phone
                    if contents is not None and self.is_raw_user(hex(name_address)):
                        name_addresses.append(name_address)
                        raw_users.append(contents)

        # Second, find users who are next in memory to the users previously found
        name_addresses.sort()  # In increasing order
        new_name_addresses = []
        for name_address in name_addresses:
            next_name_address = name_address + distance_between_users
            while next_name_address not in name_addresses and next_name_address not in new_name_addresses and self.is_raw_user(
                    hex(next_name_address)):
                contents: bytes = extract_surroundings(self.memory_data_path, hex(next_name_address), 0,
                                                       user_subpattern_size)
                if contents is not None:
                    raw_users.append(contents)
                    new_name_addresses.append(next_name_address)
                    next_name_address += distance_between_users
                else:
                    break

        name_addresses.sort(reverse=True)  # In decreasing order
        for name_address in name_addresses:
            next_name_address = name_address - distance_between_users
            while next_name_address not in name_addresses and next_name_address not in new_name_addresses and self.is_raw_user(
                    hex(next_name_address)):
                contents: bytes = extract_surroundings(self.memory_data_path, hex(next_name_address), 0,
                                                       user_subpattern_size)
                if contents is not None:
                    raw_users.append(contents)
                    new_name_addresses.append(next_name_address)
                    next_name_address = next_name_address - distance_between_users
                else:
                    break

        return raw_users

    def extract_conversations(self) -> List[bytes]:
        pass

    def extract_messages(self) -> List[bytes]:
        pass

    def extract_message_attachments(self) -> List[bytes]:
        pass

    def is_raw_user(self, address: str) -> bool:
        """Determine if the data stored around the address supplied corresponds to a user"""
        address_as_int = int(address, 16)
        qstring_offsets: List[int] = [self.user_offsets['name'], self.user_offsets['firstname'],
                                      self.user_offsets['lastname'], self.user_offsets['username'],
                                      self.user_offsets['phone']]

        for qstring_offset in qstring_offsets:
            # Obtain the address in little endian
            qstring_contents_address: bytes = extract_surroundings(self.memory_data_path,
                                                                   hex(address_as_int + qstring_offset), 0, 8)
            if qstring_contents_address is not None:
                # Transform the address to big endian
                qstring_contents_address_as_bytearray = bytearray(qstring_contents_address)
                qstring_contents_address_as_bytearray.reverse()
                if not self.is_address_of_qstring_contents(bytes(qstring_contents_address_as_bytearray).hex()):
                    return False
            else:
                return False

        return True

    def extract_qstring_text(self, address: str) -> str:
        """Extract the text of the first QString object found after the address supplied"""
        address_as_int: int = int(address, 16)
        qstring_contents_pattern = self.qstring_contents_patterns['less_strict']
        for filename in os.listdir(self.memory_data_path):
            if filename.endswith('.dmp'):
                region_base_address: int = int(filename.split('_')[0], 16)
                region_size: int = int(filename.split('_')[1].split('.')[0], 16)
                if region_base_address <= address_as_int < region_base_address + region_size:
                    start_offset: int = address_as_int - region_base_address
                    with open(os.path.join(self.memory_data_path, filename), mode='rb') as file_object:
                        with mmap.mmap(file_object.fileno(), length=0, access=mmap.ACCESS_READ) as mmap_object:
                            match = qstring_contents_pattern.search(mmap_object, start_offset)
                            if match is not None:
                                match_contents: bytes = match.group()
                                text_length: bytes = match_contents[4:8]
                                text_length_as_int: int = struct.unpack('<i', text_length)[0]
                                return match_contents[24:24 + text_length_as_int * 2].decode('utf-16-le')

    def is_address_of_qstring_contents(self, address: str) -> bool:
        """Find out if the given address points to the contents of a QString object"""
        address_as_int: int = int(address, 16)
        qstring_contents_pattern = self.qstring_contents_patterns['less_strict']
        for filename in os.listdir(self.memory_data_path):
            if filename.endswith('.dmp'):
                region_base_address: int = int(filename.split('_')[0], 16)
                region_size: int = int(filename.split('_')[1].split('.')[0], 16)
                if region_base_address <= address_as_int < region_base_address + region_size:
                    start_offset: int = address_as_int - region_base_address
                    with open(os.path.join(self.memory_data_path, filename), mode='rb') as file_object:
                        with mmap.mmap(file_object.fileno(), length=0, access=mmap.ACCESS_READ) as mmap_object:
                            match = qstring_contents_pattern.search(mmap_object, start_offset)
                            if match is not None and match.start() == start_offset:
                                return True
        return False


def find_matches(memory_data_path: str, regex) -> List[bytes]:
    """Find all the matches of a pattern in the memory data"""
    matches: List[bytes] = []
    for filename in os.listdir(memory_data_path):
        if filename.endswith('.dmp'):
            with open(os.path.join(memory_data_path, filename), mode='rb') as file_object:
                with mmap.mmap(file_object.fileno(), length=0, access=mmap.ACCESS_READ) as mmap_object:
                    for match in regex.finditer(mmap_object):
                        matches.append(match.group())
    return matches


def find_matches_and_their_addresses(memory_data_path: str, regex) -> List[Tuple[bytes, str]]:
    """Find all the matches of a pattern in the memory data and the addresses where the matches were found"""
    matches: List[Tuple[bytes, str]] = []
    for filename in os.listdir(memory_data_path):
        if filename.endswith('.dmp'):
            with open(os.path.join(memory_data_path, filename), mode='rb') as file_object:
                with mmap.mmap(file_object.fileno(), length=0, access=mmap.ACCESS_READ) as mmap_object:
                    for match in regex.finditer(mmap_object):
                        region_base_address: str = filename.split('_')[0]
                        match_address: int = int(region_base_address, 16) + match.start()
                        matches.append((match.group(), hex(match_address)))
    return matches


def extract_surroundings(memory_data_path: str, address: str, above_bytes_count: int, below_bytes_count: int) -> bytes:
    """Extract the contents around an address"""
    address_as_int: int = int(address, 16)
    for filename in os.listdir(memory_data_path):
        if filename.endswith('.dmp'):
            region_base_address: int = int(filename.split('_')[0], 16)
            region_size: int = int(filename.split('_')[1].split('.')[0], 16)
            if region_base_address <= address_as_int < region_base_address + region_size:
                start_offset: int = address_as_int - region_base_address
                if address_as_int - above_bytes_count >= region_base_address and address_as_int + below_bytes_count < region_base_address + region_size:
                    with open(os.path.join(memory_data_path, filename), mode='rb') as file_object:
                        with mmap.mmap(file_object.fileno(), length=0, access=mmap.ACCESS_READ) as mmap_object:
                            return mmap_object[start_offset - above_bytes_count: start_offset + below_bytes_count]
