"""
`Flake8 <https://github.com/PyCQA/flake8>`_ integration.
"""
from typing import Dict, Iterator, Sequence, Union

from pathlib import Path

from . import generics, typing


# pylint: disable=unused-argument
def _filter(path: Path, message: str, line_number: int, cache: Dict[Path, Sequence[str]]) -> bool:
    """
    Return True if we want to skip the check else False if we want this check
    """
    return False
# pylint: enable=unused-argument


def compare_with_main_branch() -> Iterator[Union[typing.Lint, typing.FiltersType]]:
    """
    Compare all flake8 messages against code different to target branch.
    """
    config_argument = "--config=config.d/.flake8" if Path("config.d/.flake8").exists() else ""
    command = " ".join(("flake8", config_argument, "{lint_file}"))
    return generics.lint_compare_with_main_branch(
        execute_command=command,
        filters=(_filter,)
    )
