"""
`PyLint <https://github.com/PyCQA/pylint>`_ integration.
"""
from typing import Callable, Dict, Iterator

import re
from pathlib import Path

from . import generics, typing


def _filter(path: Path, message: str, line_number: int, cache: Dict[str, str]) -> bool:
    """
    Return True if we want to skip the check else False if we want this check
    """
    test_files = re.compile(r"(test_.*|conftest)\.py")  # pylint:

    if test_files.search(path.name):
        if path not in cache:
            cache[path] = path.read_bytes().decode().splitlines()

        content = cache[path]

        line_content = content[line_number - 1]
        if "def test_" in line_content:
            if '(missing-function-docstring)' in message:
                return True

        if ' (missing-module-docstring)' in message:
            return True

        if " (protected-access)" in message:
            return True

    if re.search(r"TODO: SPACE-\d+: ", message, re.IGNORECASE):  # ignore all TODO's marked with Jira reference
        return True

    return False


def compare_with_main_branch(filters: Callable = (_filter, )) -> Iterator[typing.Lint]:
    """
    Compare all pylint messages against code different to target branch.
    """
    config_argument = "--rcfile=config.d/pylintrc" if Path("config.d/pylintrc").exists() else ""
    command = " ".join(("pylint", config_argument, "{lint_file}"))
    return generics.lint_compare_with_main_branch(
        execute_command=command,
        filters=filters
    )
