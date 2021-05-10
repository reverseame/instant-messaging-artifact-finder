from enum import Enum
from typing import List, Tuple, Dict, Any
import argparse
import os

from artifacts.generic import Artifact, Account, User
from factories import InstantMessagingPlatformFactory, TelegramDesktopFactory
from extractors import ArtifactExtractor
from analyzers import ArtifactAnalyzer
from writers import Writer, JsonWriter


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

    def find_accounts(self) -> List[Account]:
        raw_users: List[bytes] = self.artifact_extractor.extract_users()
        users: List[User] = []
        for raw_user in raw_users:
            user_data: Dict[str, Any] = self.artifact_analyzer.analyze_user(raw_user)
            user: User = self.platform_factory.create_user(user_data)
            if user is not None:
                users.append(user)

        account: Account = self.platform_factory.create_account({'users': users})
        return [account]

    def generate_report(self, artifacts: List[Artifact]) -> None:
        if self.report_format != ReportFormat.NO_REPORT:
            self.writer.write(artifacts)


def validate_memory_data_path(memory_data_path) -> None:
    """Validate that the directory exists and that it contains at least one .dmp file"""
    if not os.path.isdir(memory_data_path):
        raise FileNotFoundError('The directory supplied does not exist')

    if not any(filename.endswith('.dmp') for filename in os.listdir(memory_data_path)):
        raise FileNotFoundError('There are no .dmp files in the directory supplied')


def validate_arguments() -> Tuple[str, InstantMessagingPlatform, ReportFormat]:
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

    arguments: Tuple[str, InstantMessagingPlatform, ReportFormat] = (memory_data_path, platform, report_format)
    return arguments


def find_artifacts(memory_data_path: str, platform: InstantMessagingPlatform, report_format: ReportFormat) -> None:
    artifact_finder: ArtifactFinder = ArtifactFinder(memory_data_path, platform, report_format)
    accounts: List[Account] = artifact_finder.find_accounts()
    artifact_finder.generate_report(accounts)


def execute() -> None:
    try:
        validated_arguments: Tuple[str, InstantMessagingPlatform, ReportFormat] = validate_arguments()
        find_artifacts(validated_arguments[0], validated_arguments[1], validated_arguments[2])
    except FileNotFoundError as fnf_error:
        print('Error:', fnf_error)
    except NotImplementedError as nie_error:
        print('Error:', nie_error)
    except ValueError as value_error:
        print('Error:', value_error)
    except Exception as exception:
        print('Error:', exception)


def main():
    execute()


if __name__ == '__main__':
    main()
