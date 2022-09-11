"""
`Mypy: Static Typing for Python <https://github.com/python/mypy>`_ integration.
"""
from typing import Dict, Iterable, Iterator, Optional, Sequence, Union

import logging
import re
import sys
import tempfile
from pathlib import Path

import bash
from mypy import errorcodes

from . import generics, git, typing

LOG = logging.getLogger(__name__)

CONFIG_FILE = "config.d/mypy.ini"


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

    if len(fields) == 1 and re.search(r"Found .* errors in .* file|"
                                      r"Success: no issues found in", fields[0]):
        return None

    if fields == ['']:
        return None

    raise ValueError(str(fields))


def _filter(path: Path, message: str, line_number: int, cache: Dict[Path, Sequence[str]]) -> bool:
    """
    Return True if we want to skip the check else False if we want this check
    """
    # pylint: disable=too-many-return-statements

    # pylint: disable=duplicate-code

    if generics.TEST_FILES_REGEX.search(path.name):
        if path not in cache:
            cache[path] = path.read_bytes().decode().splitlines()

        content = cache[path]

        line_content = content[line_number - 1]

        # pylint: disable=c-extension-no-member
        # if a function have a 'dummy' or 'mock' in word in its name
        # then it can be skipped for check
        if all((
            f" [{errorcodes.NO_UNTYPED_DEF.code}]" in message,
            re.search(r'def .*(dummy|mock).*\(', line_content),
        )):
            return True

        # mock a transient attribute
        # e.g.
        # mock.patch.object(generics.git, "changes", return_value={
        # test_b.py:78 Module has no attribute "git" [attr-defined]
        if all((
                f" [{errorcodes.ATTR_DEFINED.code}]" in message,
                re.search(r'mock\.patch\.object\(', line_content),
        )):
            return True
    # pylint: enable=duplicate-code

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


def _parse_message_line(message: str) -> Sequence[str]:
    return message.split(":", 3)  # filepath, line number, level, message


def compare_with_main_branch(
        filters: Iterable[typing.FiltersType] = (_filter,)
) -> Iterator[Union[typing.Lint, typing.FiltersType]]:
    """
    Compare mypy putput against target branch
    """

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

    config_argument = f"--config-file={CONFIG_FILE}" if Path(CONFIG_FILE).exists() else ""
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
