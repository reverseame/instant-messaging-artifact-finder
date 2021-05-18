import abc
from typing import Any, Dict, List


class ArtifactOrganizer(metaclass=abc.ABCMeta):
    """Interface that each concrete IM platform artifact organizer has to implement."""

    @abc.abstractmethod
    def organize(self, accounts: List[Dict[str, Any]], users: List[Dict[str, Any]], conversations: List[Dict[str, Any]],
                 messages: List[Dict[str, Any]], message_attachments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        raise NotImplementedError


class TelegramDesktopArtifactOrganizer(ArtifactOrganizer):

    def organize(self, accounts: List[Dict[str, Any]], users: List[Dict[str, Any]], conversations: List[Dict[str, Any]],
                 messages: List[Dict[str, Any]], message_attachments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:

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
