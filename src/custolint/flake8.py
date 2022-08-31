"""
`Flake8 <https://github.com/PyCQA/flake8>`_ integration.
"""
from typing import Iterator
from pathlib import Path

from . import generics, typing


def compare_with_main_branch() -> Iterator[typing.Lint]:
    """
    Compare all flake8 messages against code different to target branch.
    """
    config_argument = "--config=config.d/.flake8" if Path("config.d/.flake8").exists() else ""
    command = " ".join(("flake8", config_argument, "{lint_file}"))
    return generics.lint_compare_with_main_branch(command)
