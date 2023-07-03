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
from typing import Dict, Iterable, Iterator, Optional, Sequence, Union

import re
from pathlib import Path

from . import _typing, env, generics
from .contributors import Contributors


def _filter_test_function(message: str, line_content: str) -> bool:  # pylint: disable=too-many-return-statements
    # :check-description: test methods does not require to provide docstring
    if "def test_" in line_content:
        if '(missing-function-docstring)' in message:
            return True

    # :check-description: fixtures in test does not require to provide docstring
    # e.g. def mock_get_data(*_, **__):
    if 'def mock_' in line_content:
        return True

    if ' (missing-module-docstring)' in message:
        return True

    if " (protected-access)" in message:
        return True

    if " (too-many-public-methods)" in message:
        return True

    if 'R0801: Similar lines in ' in message:
        return True

    return False


def _filter_all_function(message: str,
                         line_content: str,
                         previous_line_content: Optional[str]) -> bool:
    # :check-description:
    # if function has embedded the description in the name do not ask for additional description
    # e.g. ``def is_valid_target(``, ``update_calculation_id`` TODO: check for verbs in future
    if all((
            ' (missing-function-docstring)' in message,
            re.search(r"^\s*def (\w{4,}|is|has|do)_\w{4,}(_\w{4,}|id)+\(", line_content)
    )):
        return True

    # :check-description: if a property then do not ask for a description
    if all(
            ('@property' in (previous_line_content or ''),
             ' (missing-function-docstring)' in message
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


def _filter_pydantic(message: str,
                     previous_line_content: Optional[str]) -> bool:

    # :check-description: if validator of pydantic then cls is ok
    if all(
            ('@validator(' in (previous_line_content or ''),
             ' should have "self" as first argument (no-self-argument)' in message
             )):
        return True

    return False


def _filter(path: Path, message: str, line_number: int, cache: Dict[Path, Sequence[str]]) -> bool:
    """
    Return True if we want to skip the check else False if we want this check
    """
    # pylint: disable=too-many-return-statements

    if path not in cache:
        cache[path] = path.read_bytes().decode().splitlines()

    content = cache[path]

    line_content = content[line_number - 1]
    previous_line_content = content[line_number - 2] if line_number - 2 >= 0 else None

    if generics.TEST_FILES_REGEX.search(path.name):
        do_filter = _filter_test_function(message, line_content)
        if do_filter:
            return True

    do_filter = _filter_pydantic(message, previous_line_content)
    if do_filter:
        return True

    return _filter_all_function(message, line_content, previous_line_content)


def compare_with_main_branch(
        filters: Iterable[_typing.FiltersType] = (_filter, )
) -> Iterator[Union[_typing.Lint, _typing.FiltersType]]:
    """
    Compare all pylint messages against code different to target branch.
    """
    config = Path(env.CONFIG_D, 'pylintrc')
    config_argument = f"--rcfile={config}" if config.exists() else ""
    command = " ".join(("pylint", config_argument, "{lint_file}"))

    return generics.lint_compare_with_main_branch(
        execute_command=command,
        filters=filters
    )


def cli(contributors: Contributors, halt_on_n_messages: int, halt: bool = True) -> int:
    """Provide interface for pylint CLI"""
    return generics.filer_output(compare_with_main_branch(), contributors, halt_on_n_messages, halt)
