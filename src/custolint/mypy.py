"""
`Mypy: Static Typing for Python <https://github.com/python/mypy>`_ integration.
"""
from typing import Callable, Dict, Iterator, Optional, Sequence

import logging
import re
import sys
import tempfile
from pathlib import Path

import bash

from . import git, typing

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

            return (
                file_name,
                int(line_number),
                message.strip(),
                contributor['email'],
                contributor['date']
            )
        return None

    if len(fields) == 1 and re.search(r"Found .* errors in .* file|"
                                      r"Success: no issues found in", fields[0]):
        return None

    if fields == ['']:
        return None

    raise ValueError(str(fields))


def _filter(path: Path, message: str, line_number: int, cache: Dict[Path, str]) -> bool:
    """
    Return True if we want to skip the check else False if we want this check
    """
    # pylint: disable=too-many-return-statements

    # pylint: disable=duplicate-code
    test_files = re.compile(r"(test_.*|conftest)\.py")

    if test_files.search(path.name):
        if path not in cache:
            cache[path] = path.read_bytes().decode().splitlines()

        content = cache[path]

        line_content = content[line_number - 1]

    # pylint: enable=duplicate-code

        if "def test_" in line_content:

            if "Function is missing a type annotation" in message:
                return True

            print(line_content, message, "[type-arg]" in message)
            if "[type-arg]" in message:
                return True

            if '[no-untyped-def]' in message:
                return True

            if '[attr-defined]' in message:
                return True

            if 'Use "-> None" if function does not return a value' in message:
                return True

            if 'dict-item' in message:
                return True

    return False


def compare_with_main_branch(filters: Callable = (_filter,)) -> Iterator[typing.Lint]:
    """
    Compare mypy putput against target branch
    """

    changes = git.changes()

    includes = re.compile(r'.py$')
    excludes = re.compile(r"/setup.py")

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

    LOG.info("execute command %r", execute_command)
    command = bash.bash(execute_command)
    if command.stderr:
        logging.error('Mypy command failed: %s', command.stderr.decode())
        sys.exit(command.code)

    stdout = command.stdout.decode()

    for filter_item in filters:
        yield filter_item

    for mypy_line in stdout.split("\n"):
        fields = mypy_line.split(":", 3)  # filepath, line number, level, message

        results = _process_line(fields, changes)
        if results:
            yield results
