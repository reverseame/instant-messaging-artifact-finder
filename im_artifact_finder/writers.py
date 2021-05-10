import abc
from typing import List

from artifacts.generic import Artifact
from artifacts.utils import json_representation


class Writer(metaclass=abc.ABCMeta):
    """Interface that each concrete writer has to implement."""

    @abc.abstractmethod
    def write(self, artifacts: List[Artifact]) -> None:
        raise NotImplementedError


class JsonWriter(Writer):
    def write(self, artifacts: List[Artifact]) -> None:
        with open('report.json', 'w', encoding='utf-8') as report:
            report.write(json_representation(artifacts))
