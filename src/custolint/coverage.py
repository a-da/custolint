from typing import Any, Dict
from typing import Any, Dict

import bash
import logging

from . import git

LOG = logging.getLogger(__name__)


def process_missing_lines(file_name: str, missing: str, changes: Dict[str, Dict[str, Any]]):
    # if "/test_" in file_name:
    #     continue

    if "-" in missing:
        if missing.endswith("->exit"):  # alike '8->exit'
            start, _ = missing.split("->exit")
            end = int(start) + 1
        elif ">" in missing:  # alike '278->280'
            start, end = missing.split("->")
        else:  # alike 36-935
            start, end = missing.split("-")
    else:
        start = int(missing)
        end = start + 1

    start_end = list(range(int(start), int(end) + 1))

    for line_number in start_end:
        contributor = changes.get(file_name, {}).get(int(line_number))
        if contributor:
            LOG.info("%s %s:%s", contributor, file_name, line_number)


def compare_with_main_branch(coverage_file_location: str) -> None:
    """
    :param coverage_file_location: TODO: use it
    :return:
    """
    changes = git.changes(git.MAIN_BRANCH)

    has_found_something = False

    execute_command = f"coverage report --data-file={coverage_file_location} --show-missing "
    # --include=space/*
    LOG.info('execute coverage command: %r', execute_command)
    command = bash.bash(execute_command)

    if command.stderr:
        exit(f'There is an unexpected exception {command.stderr}')

    command_output = command.stdout.decode()

    for coverage_line in command_output.split("\n"):

        if not coverage_line:
            continue

        # how looks a coverage line ?
        fields = coverage_line.split()

        # header is alike 'Name    Stmts   Miss Branch BrPart  Cover   Missing'
        if coverage_line.startswith("Name "):
            continue

        # footer
        if coverage_line.startswith('TOTAL '):
            continue

        # alike 'care/__init__.py 6 0 0 0 100%'
        if fields[-1] == "100%":
            continue

        # alike
        # $ coverage report --data-file=.coverage --show-missing
        # Name                        Stmts   Miss Branch BrPart  Cover   Missing
        # -----------------------------------------------------------------------
        # src/custolint/__init__.py       5      0      0      0   100%
        # src/custolint/git.py           50      4     24      2    89%   25-26, 39-40
        # tests/test_custolint.py        22      0      2      0   100%
        # -----------------------------------------------------------------------
        # TOTAL                          77      4     26      2    92%

        if len(fields) > 4 and "Missing" not in fields[-1]:
            missing_coverage_lines = "".join(fields[6:]).split(",")

            for missing in missing_coverage_lines:
                process_missing_lines(
                    file_name=fields[0],
                    missing=missing,
                    changes=changes
                )

    if not has_found_something:
        LOG.info("::Dry and Clean::")
