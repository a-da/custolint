"""
==============================================================================
`Mypy: Static Typing for Python <https://github.com/python/mypy>`_ integration
==============================================================================

Logic:
------

1. Find affected files

.. code-block:: bash

    $ git diff origin/main -U0 --diff-filter=ACMRTUXB
    INFO:custolint.git:Git diff detected 16 filed affected

2. Executing Mypy typing only on affected file

.. code-block:: bash

    $ mypy --config-file==config.d/.flake8 test_file1.py ... file16.py
    TODO: add a real example
    test_file1.py: message function does not return a value
    ...
    file16.py: message

.. important:: if no configuration is provided custolint will fallback into strict mode

    .. code-block:: bash

        $ mypy --strict --show-error-codes file1.py ... file16.py


Filter all original Mypy message with custolint rules
-----------------------------------------------------

.. code-block:: bash
    :caption: Final Mypy custolint command

    $ custolint mypy
    file16.py: message
"""
from typing import Dict, Iterable, Iterator, Optional, Sequence, Union

import logging
import re
import sys
import tempfile
from pathlib import Path

import bash
from mypy import errorcodes

from . import env, generics, git, typing

LOG = logging.getLogger(__name__)


def _process_line(fields: Sequence[str], changes: typing.Changes) -> Optional[typing.Lint]:
    """
    Process a single line message from MyPy report
    """
    if len(fields) == 4:

        file_name = fields[0]
        line_number = int(fields[1])
        message: str = fields[-1]

        contributor = changes.get(file_name, {}).get(line_number)
        if contributor:

            return typing.Lint(
                file_name=file_name,
                line_number=int(line_number),
                message=message.strip(),
                email=contributor['email'],
                date=contributor['date']
            )
        return None

    if len(fields) == 1:
        if re.search(r"Found .+ errors? in .+ files?", fields[0]):
            return None

    if fields == ['']:
        return None

    if len(fields) == 2 and fields[0] == "Success":
        return None

    raise ValueError(str(fields))


def _filter_test_function(message: str, line_content: str) -> bool:
    """
    SubCase of the ``_filter``function

    TODO: Check in configuration what is considered test function
    by default is ``def test_.*``
    """
    if "def test_" in line_content:
        if f" [{errorcodes.TYPE_ARG.code}]" in message:
            return True

        if f" [{errorcodes.NO_UNTYPED_DEF.code}]" in message:
            return True

        if f" [{errorcodes.ATTR_DEFINED.code}]" in message:
            return True

        if "Use \"-> None\" if function does not return a value" in message:
            return True

        if "dict-item" in message:
            return True

    return False


def _filter_test_function_attr_defined(message: str,
                                       line_content: str,
                                       previous_line_content: Optional[str]) -> bool:
    mocking_line = re.compile(r'(mock|mocker)\.patch\.object\(')

    # mock a transient attribute which is not declared in __all__
    # e.g.
    # mock.patch.object(generics.git, "changes", return_value={
    # test_b.py:78 Module has no attribute "git" [attr-defined]
    if all((
            f" [{errorcodes.ATTR_DEFINED.code}]" in message,
            mocking_line.search(line_content),
    )):
        return True

    # if the line is split check previous lineform
    if previous_line_content and all((
            f" [{errorcodes.ATTR_DEFINED.code}]" in message,
            mocking_line.search(previous_line_content),
    )):
        return True

    # It is normal practice to patch private api in tests
    # from a.b.c.d import e
    # ORIGINAL_E_GET_TIME = e._get_time
    if re.search(r'Module ".+" does not explicitly export attribute "_.+"', message):
        return True

    if 'Missing type parameters for generic type "Callable"  [type-arg]' in message:
        return True

    return False


def _filter(path: Path, message: str, line_number: int, cache: Dict[Path, Sequence[str]]) -> bool:
    """
    Return True if we want to skip the check else False if we want this check
    """
    # pylint: disable=too-many-return-statements

    # pylint: disable=duplicate-code
    if not generics.TEST_FILES_REGEX.search(path.name):
        return False

    if path not in cache:
        cache[path] = path.read_bytes().decode().splitlines()

    content = cache[path]

    line_content = content[line_number - 1]
    previous_line_content = content[line_number - 2] if line_number - 2 >= 0 else None

    # pylint: disable=c-extension-no-member
    # if a function have a 'dummy' or 'mock' in word in its name
    # then it can be skipped for check
    if all((
        f" [{errorcodes.NO_UNTYPED_DEF.code}]" in message,
        re.search(r'def .*(dummy|mock).*\(', line_content),
    )):
        return True

    do_filter = _filter_test_function_attr_defined(message, line_content, previous_line_content)
    if do_filter:
        return do_filter

    do_filter = _filter_test_function(message, line_content)
    if do_filter:
        return do_filter

    return False


def _parse_message_line(message: str) -> Sequence[str]:
    return message.split(":", 3)  # filepath, line number, level, message


def compare_with_main_branch(
        filters: Iterable[typing.FiltersType] = (_filter,)
) -> Iterator[Union[typing.Lint, typing.FiltersType]]:
    """
    Compare mypy output against target branch
    """
    # pylint: disable=too-many-locals

    changes = git.changes()

    includes = re.compile(r'\.py$')
    excludes = re.compile(r"/setup\.py")

    paths = "\n".join(i for i in changes if includes.search(i) and not excludes.search(i))

    if not paths:
        LOG.info("No file was affected")
        return

    # mypy accept a reference to a file as an argument
    _, tmp_path = tempfile.mkstemp()
    Path(tmp_path).write_text(paths)  # pylint: disable=unspecified-encoding

    config = Path(env.CONFIG_D, "mypy.ini")
    config_argument = f"--config-file={config}" if config.exists() else ""
    command_args = " ".join((
        "mypy",
        config_argument or "--strict --show-error-codes",
        "@{tmp_path}"
    ))

    execute_command = command_args.format(tmp_path=tmp_path)

    LOG.info("Execute command %r", execute_command)
    command = bash.bash(execute_command)
    if command.stderr:
        logging.error('Mypy command failed: %s', command.stderr.decode())
        sys.exit(command.code)

    stdout = command.stdout.decode()

    for filter_item in filters:
        yield filter_item

    for mypy_line in stdout.split("\n"):
        fields = _parse_message_line(mypy_line)

        results = _process_line(fields, changes)
        if results:
            yield results
