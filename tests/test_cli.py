from typing import List, Tuple

import re
import sys
from unittest import mock

from custolint import cli

import pytest


@pytest.mark.parametrize('api', (
    pytest.param(('custolint', "mypy"), id='mypy'),
    pytest.param(('custolint', "pylint"), id='pylint'),
    pytest.param(('custolint', "flake8"), id='flake8'),
    pytest.param(('custolint', "coverage", '.coverage'), id='coverage'),
))
def test_cli_compare_with_main_branch(api: List[str]):
    with mock.patch.object(cli, api[1]) as mocked:

        cli.cli(*api)

        mocked.compare_with_main_branch.assert_called_once()


def test_cli_sys_argv():
    with \
            mock.patch.object(cli, 'mypy') as mocked, \
            mock.patch.object(sys, 'argv', (None, 'mypy')):

        cli.cli()

        mocked.compare_with_main_branch.assert_called_once()


@pytest.mark.parametrize('api, message', (
    pytest.param(
        ('custolint', ),
        "Require one of argument: mypy, pylint, flake8, coverage",
        id='no-command'
    ),
    pytest.param(
        ('custolint', "no-such-command"),
        "The command 'no-such-command' is not implemented",
        id='no-such-command'
    ),
    pytest.param(
        ('custolint', "coverage"),
        "Path for coverage is missing, usually it is `.coverage`",
        id='coverage-config-missing'
    ),
))
def test_cli_errors(api: Tuple[str], message: str):
    with pytest.raises(SystemExit, match=re.escape(message)):
        cli.cli(*api)
