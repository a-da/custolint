"""
`Python Coverage <https://coverage.readthedocs.io/en/6.4.4/>`_ integration.

1. Locate uncovered code source lines
2. If the uncovered code is touched withing changes in current branch.
3. Show only not tested file name and line to be covered with unittest.

.. important:

    Please ensure set ``source`` in the configuration,
    otherwise coverage will include just files covered by the tests.

    TODO:
    See config.d/.coveragerc
    .. include: config.d/.coveragerc

    or
    .. include: setup.cfg
        from: coverage:run
        till: end coverage
"""

from typing import Iterator

import logging
import sys

import bash

from . import git, typing

LOG = logging.getLogger(__name__)


def _process_missing_lines(
        file_name: str,
        missing: str,
        changes: typing.Changes) -> Iterator[typing.Coverage]:

    if "-" in missing:
        # The condition was nether false or nether true, we will just point to the first line
        if missing.endswith("->exit"):  # alike '8->exit'
            start = end = missing.split("->exit")[0]
        elif ">" in missing:  # alike '58->56'
            start = end = missing.split("->")[0]
        else:  # alike 36-935
            start, end = missing.split("-")
    else:
        start = end = missing

    start_end = list(range(int(start), int(end) + 1))
    del start, end

    for line_number in start_end:
        contributor = changes.get(file_name, {}).get(int(line_number))
        if contributor:
            yield typing.Coverage(
                contributor=contributor,
                file_name=file_name,
                line_number=line_number
            )


def compare_with_main_branch(coverage_file_location: str) -> Iterator[typing.Coverage]:
    """
    :param coverage_file_location: TODO: use it
    :return:
    """
    changes = git.changes()

    execute_command = f"coverage report --data-file={coverage_file_location} --show-missing"
    # --include=space/*
    LOG.info('execute coverage command: %r', execute_command)

    command = bash.bash(execute_command)

    if command.code:
        logging.error('Coverage command failed: %s', (command.stderr or command.stdout).decode())
        sys.exit(command.code)

    stdout = command.stdout.decode()
    # stdout alike
    # $ coverage report --data-file=.coverage --show-missing
    # Name                        Stmts   Miss Branch BrPart  Cover   Missing
    # -----------------------------------------------------------------------
    # src/custolint/__init__.py       5      0      0      0   100%
    # src/custolint/git.py           50      4     24      2    89%   25-26, 39-40
    # tests/test_custolint.py        22      0      2      0   100%
    # -----------------------------------------------------------------------
    # TOTAL                          77      4     26      2    92%

    for coverage_line in stdout.split("\n"):

        if not coverage_line:
            continue

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

        if len(fields) > 4 and "Missing" not in fields[-1]:
            missing_coverage_lines = "".join(fields[6:]).split(",")
            for missing in missing_coverage_lines:
                for line in _process_missing_lines(
                    file_name=fields[0],
                    missing=missing,
                    changes=changes
                ):
                    yield line
