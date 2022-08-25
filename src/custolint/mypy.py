import re
import logging
import tempfile
import os
from pathlib import Path

import bash

from . import git, generics

LOG = logging.getLogger(__name__)


def compare_with_main_branch() -> None:
    LOG.info("MYPY COMPARE WITH %r branch", git.MAIN_BRANCH)
    changes = git.changes(git.MAIN_BRANCH)

    includes = re.compile(r'.py$')
    excludes = re.compile(r"/setup.py")

    paths = "\n".join(i for i in changes.keys() if includes.search(i) and not excludes.search(i))

    if not paths:
        LOG.info("No file was affected")
        return

    # mypy accept a reference to a file as an argument
    _, tmp_path = tempfile.mkstemp()
    Path(tmp_path).write_text(paths)

    has_found_something = False

    # TODO validate cmd before pass
    execute_command = (
            os.getenv("MYPY_CMD") or "mypy --strict --show-error-codes @{tmp_path}"
    ).format(tmp_path=tmp_path)

    LOG.info("execute command %r", execute_command)
    command = bash.bash(execute_command)
    if command.stderr:
        LOG.error(command.stderr)
        exit(1)

    for mypy_line in command.stdout.decode().split("\n"):
        fields = mypy_line.split(":", 3)  # filepath, line number, level, message

        if len(fields) == 4:
            file_name = fields[0]
            line_number = int(fields[1])

            contributor = changes.get(file_name, {}).get(line_number)
            if contributor:

                # FILTERS
                """
                Filter 001
                test functions always return None, make no sense to enforce return None, ignore that
                    def test_a():
                """
                if re.search(r"test_.*\.py", file_name) and "Function is missing a type annotation":
                    code_line = Path(file_name).read_text().splitlines()[line_number - 1]

                    if "def test_" in code_line:
                        continue

                # OUTPUT
                generics.output("%s %s", mypy_line, contributor)
            else:
                LOG.debug(mypy_line)

        elif fields == [""]:
            LOG.debug(mypy_line)
        else:
            if "/test/conftest.py" in mypy_line:
                if "Duplicate module named" in mypy_line:
                    continue
                if "Are you missing an __init__.py" in mypy_line:
                    continue

            if not has_found_something and re.search(r"Found \d+ errors in \d+ file", mypy_line):
                continue

            print("something wrong ", len(fields), mypy_line, fields)

    if not has_found_something:
        print("::Dry and Clean::")
