"""
API to get the affected code lines by comparing current branch to a target branch.
"""
from typing import Iterable, Iterator, Tuple, Union, cast
from collections import defaultdict

import logging
import os
import re
import sys
import json

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
        yield typing.Blame(
            file_name=file_name,
            line_number=int(index),
            email=email,
            date=date
        )


def _process_diff_line(diff_line: str, file_name: str) -> Union[str, None, Iterator[typing.Blame]]:
    # line like +++ b/care/share/calc/_methods2.py
    if diff_line.startswith("+++ "):
        _, file_name = diff_line.split("+++ ", maxsplit=1)
        return file_name[2:]

    # line like @@ -0,0 +1,146 @@
    if not diff_line.startswith("@@"):
        return None

    affected_lines = diff_line.split("+", maxsplit=1)[1].split(maxsplit=1)[0]

    if affected_lines.endswith(",0"):  # the line is deleted and have to be ignored
        return None

    return _blame(affected_lines, file_name)


def changes() -> typing.Changes:
    """
    Get diff changes of current branch against master branch and
    return a mapping of affected filename and line numbers
    """
    main_branch = _autodetect_main_branch()
    LOG.info("Compare current branch with %r branch", main_branch)

    files: typing.Changes = defaultdict(dict)

    # Add new feature
    # 1. save last main branch commit hash into custolint.d/
    # 2. compare the remote main branch with custolint.d/latest_<main>_branch_hash.txt
    # 3. If there is no connection to remote the consider true with a warning else
    # If the check fails provide hints with warning how to sync the main branch
    #
    # git_pull_rebase_command = f"git pull --rebase origin {main_branch}"
    # git_pull_rebase_result = bash.bash(git_pull_rebase_command)
    # LOG.info("Sync main branch with current branch with command %r", git_pull_rebase_command)
    #
    # if git_pull_rebase_result.code:
    #     logging.error('Sync command failed: %s', git_pull_rebase_result.stderr.decode())
    #     sys.exit(git_pull_rebase_result.code)
    #

    the_file = ""
    execute_command = f"git diff origin/{main_branch} -U0 --diff-filter=ACMRTUXB"
    LOG.info("Execute git diff command %r", execute_command)
    command = bash.bash(execute_command)

    if command.code:
        logging.error('Diff command failed: %s', command.stderr.decode())
        sys.exit(command.code)

    stdout = command.stdout.decode()
    LOG.debug('Git diff output %s', stdout)

    for line in stdout.split("\n"):

        result = _process_diff_line(line, the_file)

        if not result:
            continue

        if isinstance(result, str):
            the_file = result
            continue

        if isinstance(result, Iterable):  # pragma: no cover
            typed_result = cast(Iterable[typing.Blame], result)
            for blame in typed_result:
                change = files[blame.file_name]

                change[blame.line_number] = {
                    'email': blame.email,
                    'date': blame.date
                }
            continue

    LOG.info("Git diff detected %r filed affected", len(files))
    if LOG.isEnabledFor(logging.DEBUG):
        LOG.info("Changed files: \n%s", json.dumps(files, indent=4))

    return files
