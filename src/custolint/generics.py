from typing import Optional, Tuple

import re
import logging

import bash

from . import git

TO_LOG = False
LOG = logging.getLogger(__name__)


def output(msg: str, *args) -> None:
    if TO_LOG:
        LOG.info(msg, *args)
    else:
        print(msg % args)


def do_filter(pylint_line: str) -> bool:
    """
    Return True if we want to skip the check else False if we want this check
    """
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


def lint_compare_with_main_branch(execute_command: str) -> None:
    has_found_something = False
    changes = git.changes(git.MAIN_BRANCH)

    includes = re.compile(r'.py$')
    excludes = re.compile(r"/setup.py")

    paths = list(i for i in changes.keys() if includes.search(i) and not excludes.search(i))

    LOG.info("Execute lint commands %r for %r files ...", execute_command, len(paths))
    for lint_file in paths:  # TODO make parallel per path
        execute_command_ = execute_command.format(lint_file=lint_file)
        LOG.debug("Execute lint command: %r", execute_command_)
        command = bash.bash(execute_command_)
        for lint_line in command.stdout.decode().split("\n"):
            if do_filter(lint_line):
                continue

            file_name_line_number = _parse_message_line(lint_line)
            if file_name_line_number:
                file_name, line_number = file_name_line_number
                contributor = changes.get(file_name, {}).get(int(line_number))
                if contributor:
                    has_found_something = True
                    output("%s %s", lint_line, contributor)
            else:
                if not lint_line.strip("-"):
                    continue
                if lint_line.startswith("Your code has been rated at "):
                    continue
                if lint_line.startswith("*****"):
                    continue

                LOG.error("Can not parse lint line", lint_line)

    if not has_found_something:
        LOG.info("::Dry and Clean::")
