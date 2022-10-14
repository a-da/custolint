"""
=======================================================
`Flake8 <https://github.com/PyCQA/flake8>`_ integration
=======================================================

1. Find affected files

.. code-block:: bash

    $ git diff origin/main -U0 --diff-filter=ACMRTUXB
    INFO:custolint.git:Git diff detected 16 filed affected

2. Executing Flake8 linting only on affected file

.. code-block:: bash

    $ flake8 --config-file=config.d/.flake8 file1.py ... file16.py
    TODO: add a rela example
    file1.py: message CUSTOLINT_IGNORE_MATCH
    ...
    file16.py: message

3. Filter all original Flake8 message with custolint rules

.. code-block:: bash
    :caption: Final Flake8 custolint command

    $ custolint flake8
    file16.py: message

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
