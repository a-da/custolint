"""
API to get the affected code lines by comparing current branch to a target branch.
"""
from typing import Iterator, Tuple

import logging
import os
import re
import sys

import bash

from . import typing

LOG = logging.getLogger(__name__)

BRANCH_ENV = 'CUSTOLINT_MAIN_BRANCH'


def _autodetect_main_branch() -> str:
    """
    Autodetect main/default branch name.

    .. important: autodetect can ve override with :py:const:`.BRANCH_ENV` os ENV.
    """
    branch_name = os.getenv(BRANCH_ENV)
    if branch_name:
        command = bash.bash(f'git branch -r --list origin/{branch_name}')
        if command.code:
            logging.error('Branch name %r provided through OS env %r can not be found in git: %s',
                          branch_name, BRANCH_ENV, command.stderr.decode())
            sys.exit(command.code)

        return branch_name

    command = bash.bash('git remote show origin')
    if command.code:
        logging.error('Could not find default/main branch: %r', command.stderr.decode())
        sys.exit(command.code)

    stdout: str = command.stdout.decode()
    return re.search(r"HEAD branch: (.+)", stdout).group(1)  # type: ignore[union-attr]


def _extract_email_and_date_from_blame(blame_line: str) -> Tuple[str, str]:
    """
    Extract email and date from blame message line
    """
    _, tail = blame_line.split("<", maxsplit=1)
    email, tail = tail.split(">", maxsplit=1)
    date, _ = tail.split(maxsplit=1)
    return email, date


def _blame(the_line_number: str, file_name: str) -> Iterator[typing.Blame]:
    if "-" in the_line_number:
        start, ends = [int(_) for _ in the_line_number.split("-")]
        plus_start = ends - start
    elif "," in the_line_number:
        start, plus_start = [int(_) for _ in the_line_number.split(",")]
    else:
        plus_start = 1
        start = int(the_line_number)

    # git blame -L 33,+1 --show-email -- helpers/src/banana_sdk/helpers/service_api/metadata.py
    # 6d2056da7 (<saul.goodman@some-domain.com> 2020-06-03 14:11:42 +0200 33)  if event_count > 0:
    execute_command = f"git blame -L {start},+{plus_start} --show-email --  {file_name}"
    LOG.debug("Execute git blame command: %r", execute_command)
    command = bash.bash(execute_command)

    if command.code:
        logging.error('Blame command failed: %s', command.stderr.decode())
        sys.exit(command.code)

    stdout = command.stdout.decode().strip()

    for index, line in enumerate(stdout.split("\n"), start=start):
        email, date = _extract_email_and_date_from_blame(line)
        yield file_name, index, email, date


def changes() -> typing.Changes:
    """
    Get diff changes of current branch against master branch and
    return a mapping of affected filename and line numbers
    """
    main_branch = _autodetect_main_branch()
    LOG.info("Compare current branch with %r branch", main_branch)

    files: typing.Changes = {}

    the_file = ""
    execute_command = f"git diff origin/{main_branch} -U0 --diff-filter=ACMRTUXB"
    LOG.info("Execute git diff command %r", execute_command)
    command = bash.bash(execute_command)

    if command.code:
        logging.error('Diff command failed: %s', command.stderr.decode())
        sys.exit(command.code)

    stdout = command.stdout.decode()
    for line in stdout.split("\n"):

        # line like +++ b/care/share/calc/_methods2.py
        if line.startswith("+++ "):
            _, the_file = line.split("+++ ", maxsplit=1)
            the_file = the_file[2:]
            continue

        # line like @@ -0,0 +1,146 @@
        if line.startswith("@@"):
            affected_lines = line.split("+", maxsplit=1)[1].split(maxsplit=1)[0]

            if affected_lines.endswith(",0"):  # the line is deleted and have to be ignored
                continue

            for _, index, email, date in _blame(
                    the_line_number=affected_lines,
                    file_name=the_file):

                if the_file not in files:
                    files[the_file] = {}

                files[the_file][index] = {
                    'email': email,
                    'date': date
                }

    LOG.info("Git diff detected %r filed affected", len(files))
    return files
