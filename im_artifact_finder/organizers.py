import abc
from typing import Any, Dict, List
import logging

from artifacts.generic import Account, User

logger = logging.getLogger(__name__)


class ArtifactOrganizer(metaclass=abc.ABCMeta):
    """Interface that each concrete IM platform artifact organizer has to implement."""

    @abc.abstractmethod
    def organize_before_creation(self, accounts: List[Dict[str, Any]], users: List[Dict[str, Any]],
                                 conversations: List[Dict[str, Any]], messages: List[Dict[str, Any]],
                                 message_attachments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        raise NotImplementedError

    @abc.abstractmethod
    def organize_after_creation(self, accounts: List[Account]) -> List[Account]:
        raise NotImplementedError


class TelegramDesktopArtifactOrganizer(ArtifactOrganizer):

    def organize_before_creation(self, accounts: List[Dict[str, Any]], users: List[Dict[str, Any]],
                                 conversations: List[Dict[str, Any]], messages: List[Dict[str, Any]],
                                 message_attachments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:

        # Identify all the conversations.
        conversations: List[Dict[str, Any]] = []
        for message_data in messages:
            if 'conversation' in message_data and 'id' in message_data['conversation'] and 'account_owner_id' in \
                    message_data['conversation']:
                if not is_conversation_repeated(conversations, message_data['conversation']):
                    message_data['conversation']['messages'] = []
                    conversations.append(message_data['conversation'])

        # Place each message in the right conversation.
        for message_data in messages:
            if 'conversation' in message_data and 'id' in message_data['conversation'] and 'account_owner_id' in \
                    message_data['conversation']:
                insert_message_in_right_conversation(conversations, message_data)

        # Place the users and conversations in their respective accounts.
        account_owner_ids: List[int] = []
        for user in users:
            if user['account_owner_id'] not in account_owner_ids:
                account_owner_ids.append(user['account_owner_id'])
        for conversation in conversations:
            if conversation['account_owner_id'] not in account_owner_ids:
                account_owner_ids.append(conversation['account_owner_id'])

        logger.info(f'Number of account owners identified: {len(account_owner_ids)}')

        organized_accounts_by_owner_id: Dict[int, Dict[str, Any]] = {}
        for account_owner_id in account_owner_ids:
            organized_accounts_by_owner_id[account_owner_id] = {'owner': find_user_by_id(users, account_owner_id),
                                                                'users': [],
                                                                'conversations': []}

        for user in users:
            if user['account_owner_id'] in organized_accounts_by_owner_id:
                organized_accounts_by_owner_id[user['account_owner_id']]['users'].append(user)

        for conversation in conversations:
            if conversation['account_owner_id'] in organized_accounts_by_owner_id:
                organized_accounts_by_owner_id[conversation['account_owner_id']]['conversations'].append(conversation)

        organized_accounts_as_list: List[Dict[str, Any]] = []
        for account_owner_id in organized_accounts_by_owner_id:
            organized_accounts_as_list.append(organized_accounts_by_owner_id[account_owner_id])

        return organized_accounts_as_list

    def organize_after_creation(self, accounts: List[Account]) -> List[Account]:
        return accounts


def is_conversation_repeated(conversations: List[Dict[str, Any]], conversation_data: Dict[str, Any]) -> bool:
    for conversation in conversations:
        if conversation['id'] == conversation_data['id'] and conversation['account_owner_id'] == \
                conversation_data['account_owner_id']:
            return True

    return False


def insert_message_in_right_conversation(conversations: List[Dict[str, Any]], message_data: Dict[str, Any]) -> None:
    for conversation in conversations:
        if conversation['id'] == message_data['conversation']['id'] and conversation['account_owner_id'] == \
                message_data['conversation']['account_owner_id']:
            conversation['messages'].append(message_data)


def find_repeated_users(users: List[User]) -> List[User]:
    repeated_users: List[User] = []
    unique_users: List[User] = []
    for user in users:
        if not is_user_repeated(unique_users, user):
            unique_users.append(user)
        elif is_user_repeated(unique_users, user) and not is_user_repeated(repeated_users, user):
            repeated_users.append(user)
    return repeated_users


def is_user_repeated(users: List[User], new_user: User) -> bool:
    if new_user.user_id is not None:
        for user in users:
            if user.user_id == new_user.user_id:
                return True
    return False


def find_user_by_id(users: List[Dict[str, Any]], user_id: int) -> Dict[str, Any]:
    for user in users:
        if user['id'] == user_id:
            return user
