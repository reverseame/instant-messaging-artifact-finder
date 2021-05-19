import abc
from typing import Any, Dict, List
import logging

from artifacts.generic import Account, User
from artifacts.telegram_desktop import TelegramDesktopIndividualConversation

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

        # Identify all the conversations
        conversations: List[Dict[str, Any]] = []
        for message_data in messages:
            if 'conversation' in message_data:
                if not is_conversation_repeated(conversations, message_data['conversation']):
                    message_data['conversation']['messages'] = []
                    conversations.append(message_data['conversation'])

        # Place each message in the right conversation
        for message_data in messages:
            if 'conversation' in message_data and 'id' in message_data['conversation']:
                insert_message_in_right_conversation(conversations, message_data)

        # At the moment, only one account is supported
        account_data: Dict[str, Any] = {'users': users, 'conversations': conversations}
        return [account_data]

    def organize_after_creation(self, accounts: List[Account]) -> List[Account]:
        # Right not, only one account is supported

        # Identify the owner of the account
        # If the same user is involved in 2 or more individual conversations, then that user is the account owner
        # Besides, the account owner cannot be a contact of himself/herself
        individual_conversations: List[TelegramDesktopIndividualConversation] = []
        for account in accounts:
            for conversation in account.conversations:
                if isinstance(conversation, TelegramDesktopIndividualConversation):
                    individual_conversations.append(conversation)

        if len(individual_conversations) == 1:
            if len(individual_conversations[0].users) == 2:
                first_user: User = individual_conversations[0].users[0]
                second_user: User = individual_conversations[0].users[1]
                if first_user.is_contact is False and second_user.is_contact is True and len(accounts) == 1:
                    accounts[0].owner = first_user
                elif first_user.is_contact is True and second_user.is_contact is False and len(accounts) == 1:
                    accounts[0].owner = second_user
        elif len(individual_conversations) > 1:
            non_contacts_in_individual_conversations: List[User] = []
            for individual_conversation in individual_conversations:
                if len(individual_conversation.users) == 2:
                    first_user: User = individual_conversation.users[0]
                    second_user: User = individual_conversation.users[1]
                    if first_user.is_contact is False:
                        non_contacts_in_individual_conversations.append(first_user)
                    if second_user.is_contact is False:
                        non_contacts_in_individual_conversations.append(second_user)
                elif len(individual_conversation.users) == 1:
                    unique_user: User = individual_conversation.users[0]
                    if unique_user.is_contact is False:
                        non_contacts_in_individual_conversations.append(unique_user)

            account_owners: List[User] = find_repeated_users(non_contacts_in_individual_conversations)
            logger.debug(f'Number of account owners identified: {len(account_owners)}')

            if len(account_owners) == 1 and len(accounts) == 1:
                accounts[0].owner = account_owners[0]

        return accounts


def is_conversation_repeated(conversations: List[Dict[str, Any]], conversation_data: Dict[str, Any]) -> bool:
    if 'id' in conversation_data:
        for conversation in conversations:
            if 'id' in conversation and conversation['id'] == conversation_data['id']:
                return True
    return False


def insert_message_in_right_conversation(conversations: List[Dict[str, Any]], message_data: Dict[str, Any]) -> None:
    for conversation in conversations:
        if conversation['id'] == message_data['conversation']['id']:
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
