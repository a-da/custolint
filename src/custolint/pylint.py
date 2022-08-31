"""
`PyLint <https://github.com/PyCQA/pylint>`_ integration.
"""
from typing import Iterator
from pathlib import Path

from . import generics, typing


def compare_with_main_branch() -> Iterator[typing.Lint]:
    """
    Compare all pylint messages against code different to target branch.
    """
    config_argument = "--rcfile=config.d/pylintrc" if Path("config.d/pylintrc").exists() else ""
    command = " ".join(("pylint", config_argument, "{lint_file}"))
    return generics.lint_compare_with_main_branch(command)
