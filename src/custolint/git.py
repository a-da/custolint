"""
API to get the affected code lines by comparing current branch to a target branch.
"""
from typing import Iterator, Tuple
import logging
import os
import sys

import bash

from . import typing

LOG = logging.getLogger(__name__)

MAIN_BRANCH = os.getenv('MAIN_BRANCH') or 'develop'


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
    if command.stderr:
        sys.exit(command.stderr.decode())

    stdout = command.stdout.decode().strip()

    for index, line in enumerate(stdout.split("\n"), start=start):
        email, date = _extract_email_and_date_from_blame(line)
        yield file_name, index, email, date


def changes(main_branch: str) -> typing.Changes:
    """
    Get diff changes of current branch against master branch and
    return a mapping of affected filename and line numbers
    """

    files: typing.Changes = {}

    the_file = ""
    execute_command = f"git diff origin/{main_branch} -U0 --diff-filter=ACMRTUXB"
    LOG.info("Execute git diff command %r", execute_command)
    command = bash.bash(execute_command)
    if command.stderr:
        sys.exit(command.stderr.decode())

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
