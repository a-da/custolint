"""
Keep here all tools, helpers and utility API.
"""
from typing import Dict, Iterable, Iterator, List, Optional, Sequence, Tuple, Union

import builtins
import logging
import re
import sys
from pathlib import Path

import bash

from . import git, typing

LOG = logging.getLogger(__name__)

TEST_FILES_REGEX = re.compile(r"(^|/)(test_.*|conftest)\.py")


def output(msg: str, *args: Union[str, int], log: Optional[logging.Logger] = None) -> None:
    """
    A unified version of output to stdout or log.
    """
    if log:
        log.info(msg, *args)
    else:
        builtins.print(msg % args)


def _parse_message_line(stdout_line: str) -> Optional[Tuple[str, int, str]]:
    """
    >> pylint_parse_message_line("cli/test/test_cli.py:100:4:")
    (cli/test/test_cli.py, 100)
    """
    # cli/test/test_cli.py:100:4: message

    # expected not parsable lines
    if not stdout_line.strip("-"):
        return None

    if stdout_line.startswith("Your code has been rated at "):
        return None

    if stdout_line.startswith("*****"):
        return None

    match = re.search(r"(^.+?):(\d+):(.+)", stdout_line)
    if match:
        file_name = match.group(1)
        line_number = int(match.group(2))
        message = match.group(3)
        return file_name, line_number, message

    # unexpected not parsable lines
    raise RuntimeError(f"Can not parse lint line {stdout_line!r}")


def _process_line(fields: Tuple[str, int, str], changes: typing.Changes) -> Optional[typing.Lint]:
    """
    Process a single line message from PyLint or Flake8 report
    """
    file_name = fields[0]
    line_number = fields[1]
    message = fields[2]

    contributor = changes.get(file_name, {}).get(line_number)

    if contributor:
        return typing.Lint(
            file_name=file_name,
            line_number=line_number,
            message=message,
            email=contributor['email'],
            date=contributor['date']
        )

    return None


def lint_compare_with_main_branch(
        execute_command: str,
        filters: Iterable[typing.FiltersType]) -> Iterator[Union[typing.Lint, typing.FiltersType]]:
    """
    A common API for pylint and flake8
    """
    # pylint: disable=too-many-locals
    changes = git.changes()

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
        logging.error('Lint command failed: %s', command.stderr.decode())
        sys.exit(command.code)

    stdout = command.stdout.decode()

    for filter_item in filters:
        yield filter_item

    LOG.debug('Lint stdout: %s', stdout)

    similar_line = None

    for lint_line in stdout.split("\n"):
        if similar_line:
            continue

        fields = _parse_message_line(lint_line)
        if not fields:
            continue

        msg = fields[2]
        if 'Similar lines in' in msg:
            similar_line = True
        else:
            similar_line = None

        results = _process_line(fields, changes)
        if results:
            yield results


def _output_grouping_by_email_and_file_name(chunk: Iterable[typing.Coverage]) -> None:
    """
    Output grouping items email and file name
    """
    iterator = iter(chunk)
    head = next(iterator)
    file_name = head[1]
    email = head[0]['email']
    date = head[0]['date']

    last = None
    for last in iterator:
        pass

    if not last:
        line_number = f"{head[2]}"
    else:
        start_line, end_line = head[2], last[2]
        line_number = f"{start_line}-{end_line}"

    output("%s:%s %05s %s", file_name, line_number, email, date)


def group_by_email_and_file_name(log: Iterable[typing.Coverage]) -> None:
    """
    Group by email and file name, used for coverage.
    """
    has_found_something = None
    previous_email = None
    previous_file_name = None
    previous_line_number = None
    chunk = []
    for line in log:
        email = line.contributor['email']
        file_name = line.file_name
        line_number = line.line_number
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
    else:
        sys.exit(41)


def filer_output(log: Iterable[Union[typing.FiltersType, typing.Lint]]) -> None:
    """
    Filter output by:
    - date range
    - include contributor
    - exclude contributor
    """
    cache: Dict[Path, Sequence[str]] = {}
    filters_chain: List[typing.FiltersType] = []

    has_found_something = False
    # get filter from env, configuration and cli
    for line in log:

        if callable(line):
            filters_chain.append(line)
            continue

        do_continue = False
        for filter_item in filters_chain:
            if filter_item(Path(line.file_name), line.message, line.line_number, cache):
                do_continue = True
                break
        if do_continue:
            continue

        output('%s:%d %s', line.file_name, line.line_number, line.message)

        has_found_something = True

    if not has_found_something:
        output("::Dry and Clean::")
    else:
        sys.exit(41)
