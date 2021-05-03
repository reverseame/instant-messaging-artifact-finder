from enum import Enum
from typing import List, Tuple
import argparse
import os

from artifacts.generic import Artifact, Account
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
        if not os.path.isdir(memory_data_path):
            raise FileNotFoundError("The directory supplied as an argument does not exist")
        if platform == InstantMessagingPlatform.TELEGRAM_DESKTOP:
            self.platform: InstantMessagingPlatform = platform
        else:
            raise ValueError("Instant messaging platform not supported")
        if report_format == ReportFormat.JSON:
            self.report_format: ReportFormat = ReportFormat.JSON
            self.writer: Writer = JsonWriter()
        elif report_format == ReportFormat.NO_REPORT:
            self.report_format: ReportFormat = ReportFormat.NO_REPORT
        else:
            raise ValueError("Report format not supported")
        if platform == InstantMessagingPlatform.TELEGRAM_DESKTOP:
            self.platform_factory: InstantMessagingPlatformFactory = TelegramDesktopFactory()
        self.artifact_extractor: ArtifactExtractor = self.platform_factory.create_artifact_extractor(memory_data_path)
        self.artifact_analyzer: ArtifactAnalyzer = self.platform_factory.create_artifact_analyzer(
            self.artifact_extractor)

    def find_accounts(self) -> List[Account]:
        pass

    def generate_report(self, artifacts: List[Artifact]) -> None:
        if self.report_format != ReportFormat.NO_REPORT:
            self.writer.write(artifacts)


def validate_arguments() -> Tuple[str, InstantMessagingPlatform, ReportFormat]:
    """Parse and validate command line arguments"""
    arg_parser = argparse.ArgumentParser(description="Find memory artifacts from instant messaging applications")
    arg_parser.version = "0.0.0"
    arg_parser.add_argument("-v",
                            "--version",
                            action="version",
                            help="show the program version and exit")
    arg_parser.add_argument("memory_data_path",
                            help="the directory path where the memory data is")
    arg_parser.add_argument("platform",
                            choices=["TELEGRAM_DESKTOP"],
                            help="instant messaging platform")
    arg_parser.add_argument("-f",
                            "--format",
                            choices=["NO_REPORT", "JSON"],
                            default="NO_REPORT",
                            help="desired report format")
    args = arg_parser.parse_args()

    memory_data_path: str = args.memory_data_path
    # Validate that the memory data path exists
    if not os.path.isdir(memory_data_path):
        raise FileNotFoundError("The directory supplied as an argument does not exist")

    platform = args.platform
    if platform == "TELEGRAM_DESKTOP":
        platform = InstantMessagingPlatform.TELEGRAM_DESKTOP
    else:
        raise ValueError("Instant messaging platform not supported")

    report_format = args.format
    if report_format == "JSON":
        report_format = ReportFormat.JSON
    elif report_format == "NO_REPORT":
        report_format = ReportFormat.NO_REPORT
    else:
        raise ValueError("Report format not supported")

    arguments: Tuple[str, InstantMessagingPlatform, ReportFormat] = (memory_data_path, platform, report_format)
    return arguments


def find_artifacts(memory_data_path: str, platform: InstantMessagingPlatform, report_format: ReportFormat):
    artifact_finder: ArtifactFinder = ArtifactFinder(memory_data_path, platform, report_format)
    accounts: List[Account] = artifact_finder.find_accounts()
    artifact_finder.generate_report(accounts)


def execute():
    try:
        validated_arguments: Tuple[str, InstantMessagingPlatform, ReportFormat] = validate_arguments()
        find_artifacts(validated_arguments[0], validated_arguments[1], validated_arguments[2])
    except FileNotFoundError as fnf_error:
        print("Error:", fnf_error)
    except NotImplementedError as nie_error:
        print("Error:", nie_error)
    except ValueError as value_error:
        print("Error:", value_error)
    except Exception as exception:
        print("Error:", exception)


def main():
    execute()


if __name__ == "__main__":
    main()
