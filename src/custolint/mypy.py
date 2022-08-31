"""
`Mypy: Static Typing for Python <https://github.com/python/mypy>`_ integration.
"""
from typing import Iterator, Optional, Sequence
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

            # FILTERS LIST:
            #
            # Filter 001
            # test functions always return None, make no sense to enforce return None, ignore that
            #    def test_a():
            # """
            if re.search(r"test_.*\.py", file_name) and \
                    "Function is missing a type annotation" in message:

                content = Path(file_name).read_text()  # pylint: disable=unspecified-encoding
                code_line = content.splitlines()[line_number - 1]

                if "def test_" in code_line:
                    return None

            return (
                file_name,
                int(line_number),
                message.strip(),
                contributor['email'],
                contributor['date']
            )
        return None

    if len(fields) == 1 and re.search("Found .* errors in .* files|"
                                      "Success: no issues found in", fields[0]):
        return None

    if fields == ['']:
        return None

    raise ValueError(str(fields))

    # if "/test/conftest.py" in file_name:
    #     if "Duplicate module named" in mypy_line:
    #         return
    #     if "Are you missing an __init__.py" in mypy_line:
    #         return
    #
    # LOG.warning("something wrong %r", fields)


def compare_with_main_branch() -> Iterator[typing.Lint]:
    """
    Compare mypy putput against target branch
    """
    LOG.info("MYPY COMPARE WITH %r branch", git.MAIN_BRANCH)
    changes = git.changes(git.MAIN_BRANCH)

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
        sys.exit(command.stderr.decode())

    stdout = command.stdout.decode()

    for mypy_line in stdout.split("\n"):
        fields = mypy_line.split(":", 3)  # filepath, line number, level, message

        results = _process_line(fields, changes)
        if results:
            yield results
