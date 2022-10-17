"""
=======================================================
`PyLint <https://github.com/PyCQA/pylint>`_ integration
=======================================================

1. Find affected files

.. code-block:: bash

    $ git diff origin/main -U0 --diff-filter=ACMRTUXB
    INFO:custolint.git:Git diff detected 16 filed affected

2. Executing PyLint typing only on affected file

.. code-block:: bash

    $ pylint --rcfile=config.d/pylintrc file1.py ... file16.py
    TODO: add a real example
    teste_file1.py: message missing-function-docstring
    ...
    file16.py: message

3. Filter all original PyLint message with custolint rules

.. code-block:: bash
    :caption: Final PyLint custolint command

    $ custolint pylint
    file16.py: message

"""
from typing import Dict, Iterable, Iterator, Sequence, Union

import re
from pathlib import Path

from . import generics, typing


def _filter(path: Path, message: str, line_number: int, cache: Dict[Path, Sequence[str]]) -> bool:
    """
    Return True if we want to skip the check else False if we want this check
    """
    # pylint: disable=too-many-return-statements

    if path not in cache:
        cache[path] = path.read_bytes().decode().splitlines()

    content = cache[path]

    line_content = content[line_number - 1]
    if generics.TEST_FILES_REGEX.search(path.name):
        if "def test_" in line_content:
            if '(missing-function-docstring)' in message:
                return True

        if ' (missing-module-docstring)' in message:
            return True

        if " (protected-access)" in message:
            return True

        if " (too-many-public-methods)" in message:
            return True

    if all((
        ' (missing-function-docstring)' in message,
        re.search(r"^\s*def \w{4,}_\w{4,}(_\w{4,})+\(", line_content)
    )):
        return True

    if all((
        ' (logging-fstring-interpolation)' in message,
        re.search(r"\w\.(critical|error|warning|info)\(", line_content)
    )):
        return True

    # ignore all TODO marked with Jira reference
    if re.search(r"TODO: [A-Z]{3,}-\d+: ", message, re.IGNORECASE):
        return True

    return False


def compare_with_main_branch(
        filters: Iterable[typing.FiltersType] = (_filter, )
) -> Iterator[Union[typing.Lint, typing.FiltersType]]:
    """
    Compare all pylint messages against code different to target branch.
    """
    config_argument = "--rcfile=config.d/pylintrc" if Path("config.d/pylintrc").exists() else ""
    command = " ".join(("pylint", config_argument, "{lint_file}"))
    return generics.lint_compare_with_main_branch(
        execute_command=command,
        filters=filters
    )
