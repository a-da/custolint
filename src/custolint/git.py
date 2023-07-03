"""
API to get the affected code lines by comparing current branch to a target branch.
"""
from typing import Iterable, Iterator, List, Optional, Tuple, Union, cast

import json
import logging
import re
import sys
from collections import defaultdict

import bash

from . import _typing, env

LOG = logging.getLogger(__name__)
MINIMUM_GIT_RECOMMEND_VERSION = (2, 39, 2)


def _autodetect_main_branch() -> str:
    """
    Autodetect main/default branch name.

    .. important: autodetect can ve override with :py:const:`custolint.env.BRANCH_ENV` os ENV.
    """
    if env.BRANCH_NAME:
        command = bash.bash(f'git branch -r --list origin/{env.BRANCH_NAME}')
        if command.code:
            logging.error('Branch name %r provided through OS env %r can not be found in git: %s',
                          env.BRANCH_NAME, env.BRANCH_ENV, command.stderr.decode())
            sys.exit(command.code)

        return env.BRANCH_NAME

    command = bash.bash('git remote show origin')
    if command.code:
        logging.error('Could not find default/main branch: %r', command.stderr.decode())
        sys.exit(command.code)

    stdout: str = command.stdout.decode()
    return re.search(r"HEAD branch: (.+)", stdout).group(1)  # type: ignore[union-attr]


def _split_as_blame_porcelain(output: str) -> Iterator[_typing.Blame]:
    buffer: List[str] = []

    # 005661f440bcdfefb2fd41d4e781351471dfb3ef 26 33 1
    head_re = re.compile(r'^[0-9a-f]{40} \d+ \d+')
    for line in output.splitlines():
        if buffer and head_re.search(line):
            yield _typing.Blame.from_porcelain(tuple(buffer))
            buffer.clear()

        buffer.append(line)

    yield _typing.Blame.from_porcelain(tuple(buffer))


def _blame(the_line_number: str, file_name: str) -> Iterator[_typing.Blame]:
    """
    Parse blame log to extract: author email, author name, date and  file_name

    > git blame --line-porcelain -L 33,+1 --show-email --show-name -- setup.cfg
    005661f440bcdfefb2fd41d4e781351471dfb3ef 26 33 1
    author John Snow
    author-mail <John.Snow@John.Snow.tld>
    author-time 1661418629
    author-tz +0200
    committer John Snow
    committer-mail <John.Snow@John.Snow.tld>
    committer-time 1661418629
    committer-tz +0200
    summary make custolint installable
    filename setup.cfg
            bash==0.6
    """
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
    execute_command = f"git blame --line-porcelain -L {start},+{plus_start} --  {file_name}"
    LOG.debug("Execute git blame command: %r", execute_command)
    command = bash.bash(execute_command)

    if command.code:
        logging.error('Blame command failed: %s', command.stderr.decode())
        sys.exit(command.code)

    stdout = command.stdout.decode().strip()

    return _split_as_blame_porcelain(stdout)


def _process_diff_line(diff_line: str, file_name: str) -> Union[str, None, Iterator[_typing.Blame]]:
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


def _current_branch_name() -> str:
    execute_command = "git branch --show-current"
    LOG.info("Execute git diff command %r", execute_command)
    command = bash.bash(execute_command)
    if command.code:
        logging.error('Could not find branch name: %s', command.stderr.decode())
        sys.exit(command.code)

    return cast(str, command.stdout.decode().strip())


def _check_git_version() -> Tuple[int, ...]:
    """
    Show a warning if the git version used is lower than was tested with by developer

    > git --version
    git version 2.39.2 (Apple Git-143)

    :return: a.b.c version format 2.39.2
    """
    execute_command = "git --version"

    LOG.debug("Execute git diff command %r", execute_command)
    command = bash.bash(execute_command)
    if command.code:
        logging.error('Could not find git version name: %s', command.stderr.decode())
        sys.exit(command.code)

    stdout = command.stdout.decode()
    versions = tuple(int(version) for version in stdout.split()[2].split('.'))
    if versions < MINIMUM_GIT_RECOMMEND_VERSION:
        LOG.warning('Be aware that current git version %r is less than recommended %r',
                    versions, MINIMUM_GIT_RECOMMEND_VERSION)

    return versions


def _pull_rebase(main_branch: str, current_branch_name: str) -> None:
    """
    git pull --rebase origin <main_branch>
    """
    execute_command = f"git pull --rebase origin {main_branch}"
    LOG.info("Execute git pull --rebase command %r", execute_command)
    command = bash.bash(execute_command)

    if command.code:
        logging.warning('Pull command failed: %s', command.stderr.decode())
        return None

    stdout = command.stdout.decode().strip()
    LOG.info("git pull: %s", stdout)

    LOG.info('HINTS: revert pull with: \n'
             '>>> git reset --hard origin/%s', current_branch_name)

    return None


def _git_sync(do_pull_rebase: bool, main_branch: str) -> Optional[str]:
    current_branch_name: Optional[str] = None

    if do_pull_rebase:
        _check_git_version()
        current_branch_name = _current_branch_name()
        _pull_rebase(main_branch, current_branch_name)

    return current_branch_name


def changes(do_pull_rebase: bool = True) -> _typing.Changes:
    """
    Get diff changes of current branch against master branch and
    return a mapping of affected filename and line numbers
    """
    main_branch = _autodetect_main_branch()
    LOG.info("Compare current branch with %r branch", main_branch)

    files: _typing.Changes = defaultdict(dict)

    _git_sync(do_pull_rebase, main_branch)

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

        if isinstance(result, Iterable):  # pragma: no cover why is not cover : TODO
            typed_result = cast(Iterable[_typing.Blame], result)
            for blame in typed_result:
                change = files[blame.file_name]

                change[blame.line_number] = {
                    'author': blame.author,
                    'email': blame.email,
                    'date': blame.date
                }
            continue

    LOG.info("Git diff detected %r filed affected", len(files))
    if LOG.isEnabledFor(logging.DEBUG):
        LOG.info("Changed files: \n%s", json.dumps(files, indent=4))

    return files
