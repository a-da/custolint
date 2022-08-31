"""
Keep here all tools, helpers and utility API.
"""
from typing import Iterator, Optional, Sequence, Tuple
import builtins
import logging
import re
import sys

import bash

from . import git, typing

TO_LOG = False
LOG = logging.getLogger(__name__)


def output(msg: str, *args: str) -> None:
    """
    A unified version of output to stdout or log.
    """
    if TO_LOG:
        LOG.info(msg, *args)
    else:
        builtins.print(msg % args)


def do_filter(pylint_line: str) -> bool:
    """
    Return True if we want to skip the check else False if we want this check
    """
    # pylint: disable=too-many-return-statements

    if "Line too long" in pylint_line:
        return True

    # special rules for test folders
    if "/test_" in pylint_line:
        if "(missing-function-docstring)" in pylint_line:
            return True

        if " function (no-self-use)" in pylint_line:
            return True

        if " (missing-module-docstring)" in pylint_line:
            return True

        if " (protected-access)" in pylint_line:
            return True

    if re.search(r"TODO: SPACE-\d+: ", pylint_line):  # ignore all TODO's marked with Jira reference
        return True

    return False


def _parse_message_line(message: str) -> Optional[Tuple[str, str]]:
    """
    >> pylint_parse_message_line("cli/test/test_cli.py:100:4:")
    (cli/test/test_cli.py, 100)
    """
    # cli/test/test_cli.py:100:4:
    match = re.search(r"(^.+?):(\d+):(\d+):", message)
    if match:
        file_name = match.group(1)
        line_number = match.group(2)
        return file_name, line_number

    return None


def lint_compare_with_main_branch(execute_command: str) -> Iterator[typing.Lint]:
    """
    A common API for pylint and flake8
    """
    # pylint: disable=too-many-locals
    changes = git.changes(git.MAIN_BRANCH)

    includes = re.compile(r'.py$')
    excludes = re.compile(r"/setup.py")

    paths = list(i for i in changes if includes.search(i) and not excludes.search(i))
    if not paths:
        return

    LOG.info("Execute lint commands %r for %r files ...", execute_command, len(paths))
    lint_files = ' '.join(i for i in paths)

    executed_command = execute_command.format(lint_file=lint_files)
    LOG.info("Execute lint command: %r", executed_command)
    command = bash.bash(executed_command)

    if command.stderr:
        LOG.error("The error was detected while running this command %r", executed_command)
        sys.exit(command.stderr.decode())

    stdout = command.stdout.decode()
    LOG.debug("pylint command output")

    for lint_line in stdout.split("\n"):

        if do_filter(lint_line):
            continue

        # TODO add parser: filename, line_number, message, apply to mypy as well
        file_name_line_number = _parse_message_line(lint_line)
        if file_name_line_number:
            file_name, line_number = file_name_line_number
            contributor = changes.get(file_name, {}).get(int(line_number))
            message = lint_line.replace(':'.join(file_name_line_number), '').strip()
            if contributor:
                yield (
                    file_name,
                    int(line_number),
                    message,
                    contributor['email'],
                    contributor['date']
                )
        else:
            if not lint_line.strip("-"):
                continue
            if lint_line.startswith("Your code has been rated at "):
                continue
            if lint_line.startswith("*****"):
                continue

            LOG.error("Can not parse lint line %r", lint_line)


def _output_grouping_by_email_and_file_name(chunk: Sequence[typing.Coverage]) -> None:
    """
    Output grouping items email and file name
    """
    file_name = chunk[0][1]
    email = chunk[0][0]['email']
    date = chunk[0][0]['date']
    if len(chunk) == 1:
        line_number = f"{chunk[0][2]}"
    else:
        start_line, end_line = chunk[0][2], chunk[-1][2]
        line_number = f"{start_line}-{end_line}"

    output("%s:%s %05s %s", file_name, line_number, email, date)


def group_by_email_and_file_name(log: Iterator[typing.Coverage]) -> None:
    """
    Group by email and file name, used for coverage.
    """
    has_found_something = None
    previous_email = None
    previous_file_name = None
    previous_line_number = None
    chunk = []
    for line in log:
        email = line[0]['email']
        file_name = line[1]
        line_number = line[2]
        has_found_something = True

        if all((
                (previous_email is None or email == previous_email),
                (previous_file_name is None or file_name == previous_file_name),
                (previous_line_number is None or previous_line_number + 1 == line_number)
        )):
            chunk.append(line)
        else:
            _output_grouping_by_email_and_file_name(chunk)
            chunk = [line]

        previous_email = email
        previous_line_number = line_number
        previous_file_name = file_name

    if chunk:
        _output_grouping_by_email_and_file_name(chunk)

    if not has_found_something:
        output("::Dry and Clean::")


def filer_output(log: Iterator[typing.Lint]) -> None:
    """
    Filter output by:
    - date range
    - include contributor
    - exclude contributor
    """
    # get filter from env, configuration and cli
    for line in log:
        # todo: apple filter condition
        output("%s " * len(line), *line)  # type: ignore[arg-type]
