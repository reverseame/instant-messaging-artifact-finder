import abc
from typing import List
import json

from artifacts.generic import Artifact
from artifacts.utils import dictionary_representation


class Writer(metaclass=abc.ABCMeta):
    """Interface that each concrete writer has to implement."""

    @abc.abstractmethod
    def write(self, artifacts: List[Artifact]) -> None:
        raise NotImplementedError


class JsonWriter(Writer):
    def write(self, artifacts: List[Artifact]) -> None:
        with open('report.json', 'w', encoding='utf-8') as report:
            report.write(json.dumps(artifacts, ensure_ascii=False, indent=4, default=dictionary_representation))
