"""
Exclude/Include contributors by name or emails with:
``--contributors`` and ``--skip-contributors``
"""
from typing import Iterable, Tuple

import logging

from pydantic import BaseModel

from custolint import _typing

LOG = logging.getLogger(__name__)


class Contributors(BaseModel):
    """
    Contributors API abstraction for CLI and GIT blame
    """
    white: Tuple[str, ...]
    black: Tuple[str, ...]

    @classmethod
    def from_cli(cls, white: str, black: str) -> 'Contributors':
        """
        Strings to Contributors
        """
        _white = cls._parse_cli_arguments(white)
        _black = cls._parse_cli_arguments(black)

        if _white and _black:
            raise ValueError('Mutually exclusion for ``white`` and ``black`` arguments')

        return cls(white=_white, black=_black)

    def _filter(self, email: str, author: str) -> bool:
        """
        Include or exclude contributors
        """
        clause = {email, author}
        if self.white:
            if not clause.intersection(self.white):
                LOG.debug('Skip %r because is not in white list of contributors %r',
                          clause, self.white)
                return True
            return False

        if self.black:
            if clause.intersection(self.black):
                LOG.debug('Skip %r because is in black list contributors %r',
                          clause, self.black)
                return True
            return False

        return False

    def filter_log_line(self, log_lines: Iterable[_typing.LogLine]) -> Iterable[_typing.LogLine]:
        """
        Include or exclude contributors from lint log line
        """
        for line in log_lines:
            if callable(line):
                yield line
                continue

            if not self._filter(line.email, line.author):
                yield line

    def filter_coverage(self, coverages: Iterable[_typing.Coverage]) -> Iterable[_typing.Coverage]:
        """
        Include or exclude contributors from coverage report
        """
        for coverage in coverages:
            if not self._filter(
                coverage.contributor['email'],
                coverage.contributor['author']
            ):
                yield coverage

    @staticmethod
    def _parse_cli_arguments(cli_argument: str) -> Tuple[str, ...]:
        return tuple(stripped for _ in cli_argument.split(',')
                     if (stripped := cli_argument.strip()))
