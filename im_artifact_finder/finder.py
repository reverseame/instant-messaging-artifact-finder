from enum import Enum
from typing import List, Tuple, Dict, Any
import argparse
import os
import shutil
import logging

from artifacts.generic import Artifact, Account
from factories import InstantMessagingPlatformFactory, TelegramDesktopFactory
from extractors import ArtifactExtractor
from analyzers import ArtifactAnalyzer
from organizers import ArtifactOrganizer
from writers import Writer, JsonWriter

default_log_level = logging.DEBUG
logging.basicConfig(level=default_log_level)
logger = logging.getLogger(__name__)


class InstantMessagingPlatform(Enum):
    TELEGRAM_DESKTOP = 1


class ReportFormat(Enum):
    NO_REPORT = 1
    JSON = 2


class ArtifactFinder:
    def __init__(self, memory_data_path: str, platform: InstantMessagingPlatform,
                 report_format: ReportFormat = ReportFormat.NO_REPORT):
        validate_memory_data_path(memory_data_path)
        if platform == InstantMessagingPlatform.TELEGRAM_DESKTOP:
            self.platform: InstantMessagingPlatform = platform
        else:
            raise ValueError('Instant messaging platform not supported')
        if report_format == ReportFormat.JSON:
            self.report_format: ReportFormat = ReportFormat.JSON
            self.writer: Writer = JsonWriter()
        elif report_format == ReportFormat.NO_REPORT:
            self.report_format: ReportFormat = ReportFormat.NO_REPORT
        else:
            raise ValueError('Report format not supported')
        if platform == InstantMessagingPlatform.TELEGRAM_DESKTOP:
            self.platform_factory: InstantMessagingPlatformFactory = TelegramDesktopFactory()
        self.artifact_extractor: ArtifactExtractor = self.platform_factory.create_artifact_extractor(memory_data_path)
        self.artifact_analyzer: ArtifactAnalyzer = self.platform_factory.create_artifact_analyzer(
            self.artifact_extractor)
        self.artifact_organizer: ArtifactOrganizer = self.platform_factory.create_artifact_organizer()

    def find_accounts(self) -> List[Account]:
        raw_accounts: List[bytes] = self.artifact_extractor.extract_accounts()
        accounts: List[Dict[str, Any]] = []
        for raw_account in raw_accounts:
            accounts.append(self.artifact_analyzer.analyze_account(raw_account))

        raw_users: List[bytes] = self.artifact_extractor.extract_users()
        users: List[Dict[str, Any]] = []
        for raw_user in raw_users:
            users.append(self.artifact_analyzer.analyze_user(raw_user))

        raw_conversations: List[bytes] = self.artifact_extractor.extract_conversations()
        conversations: List[Dict[str, Any]] = []
        for raw_conversation in raw_conversations:
            conversations.append(self.artifact_analyzer.analyze_conversation(raw_conversation))

        raw_messages: List[bytes] = self.artifact_extractor.extract_messages()
        messages: List[Dict[str, Any]] = []
        for raw_message in raw_messages:
            messages.append(self.artifact_analyzer.analyze_message(raw_message))

        raw_message_attachments: List[bytes] = self.artifact_extractor.extract_message_attachments()
        message_attachments: List[Dict[str, Any]] = []
        for raw_message_attachment in raw_message_attachments:
            message_attachments.append(self.artifact_analyzer.analyze_message_attachment(raw_message_attachment))

        organized_accounts: List[Dict[str, Any]] = self.artifact_organizer.organize_before_creation(accounts, users,
                                                                                                    conversations,
                                                                                                    messages,
                                                                                                    message_attachments)
        account_objects: List[Account] = []
        for organized_account in organized_accounts:
            account_object: Account = self.platform_factory.create_account(organized_account)
            if account_object is not None:
                account_objects.append(account_object)

        organized_account_objects: List[Account] = self.artifact_organizer.organize_after_creation(account_objects)

        return organized_account_objects

    def generate_report(self, artifacts: List[Artifact]) -> None:
        if self.report_format != ReportFormat.NO_REPORT:
            self.writer.write(artifacts)


def validate_memory_data_path(memory_data_path) -> None:
    """Validate that the directory exists and that it contains at least one .dmp file"""
    if not os.path.isdir(memory_data_path):
        raise FileNotFoundError('The memory data directory supplied does not exist')

    if not any(filename.endswith('.dmp') for filename in os.listdir(memory_data_path)):
        raise FileNotFoundError('There are no .dmp files in the directory supplied')


def validate_arguments() -> Tuple[str, InstantMessagingPlatform, ReportFormat, bool]:
    """Parse and validate command line arguments"""
    arg_parser = argparse.ArgumentParser(description='Find memory artifacts from instant messaging applications')
    arg_parser.version = '0.0.0'
    arg_parser.add_argument('-v',
                            '--version',
                            action='version',
                            help='show the program version and exit')
    arg_parser.add_argument('memory_data_path',
                            help='the directory path where the memory data is')
    arg_parser.add_argument('platform',
                            choices=['TELEGRAM_DESKTOP'],
                            help='instant messaging platform')
    arg_parser.add_argument('-f',
                            '--format',
                            choices=['JSON'],
                            default='JSON',
                            help='desired report format')
    arg_parser.add_argument('-t',
                            '--tmp',
                            help='temporary directory used to work with the memory data')
    args = arg_parser.parse_args()

    memory_data_path: str = args.memory_data_path
    validate_memory_data_path(memory_data_path)

    platform = args.platform
    if platform == 'TELEGRAM_DESKTOP':
        platform = InstantMessagingPlatform.TELEGRAM_DESKTOP
    else:
        raise ValueError('Instant messaging platform not supported')

    report_format = args.format
    if report_format == 'JSON':
        report_format = ReportFormat.JSON
    else:
        raise ValueError('Report format not supported')

    tmp_dir = args.tmp
    is_tmp_dir_supplied: bool = False
    if tmp_dir is not None:
        if os.path.isdir(tmp_dir):
            raise FileExistsError('The temporary directory supplied already exists')
        is_tmp_dir_supplied = True
        shutil.copytree(memory_data_path, tmp_dir)
        memory_data_path = tmp_dir

    arguments: Tuple[str, InstantMessagingPlatform, ReportFormat, bool] = (
        memory_data_path, platform, report_format, is_tmp_dir_supplied)
    return arguments


def find_artifacts(memory_data_path: str, platform: InstantMessagingPlatform, report_format: ReportFormat,
                   is_tmp_dir_supplied: bool) -> None:
    artifact_finder: ArtifactFinder = ArtifactFinder(memory_data_path, platform, report_format)
    accounts: List[Account] = artifact_finder.find_accounts()
    artifact_finder.generate_report(accounts)
    if is_tmp_dir_supplied:
        shutil.rmtree(memory_data_path)


def execute() -> None:
    try:
        logger.info('Execution has started')
        validated_arguments: Tuple[str, InstantMessagingPlatform, ReportFormat, bool] = validate_arguments()
        find_artifacts(validated_arguments[0], validated_arguments[1], validated_arguments[2], validated_arguments[3])
        logger.info('Execution has finished')
    except Exception as exception:
        logger.exception(exception)
        print('Error:', exception)


def main():
    execute()


if __name__ == '__main__':
    main()
