from types import ModuleType
from unittest import mock

from custolint import flake8, pylint

import pytest


@pytest.mark.parametrize('config_exists, implementation, expect_command', (
    # pylint: disable=line-too-long
    pytest.param(True, pylint, 'pylint --rcfile=config.d/pylintrc {lint_file}', id='pylint-config-exists'),
    pytest.param(False, pylint, 'pylint  {lint_file}', id='pylint-config-do-not-exists'),
    pytest.param(True, flake8, 'flake8 --config=config.d/.flake8 {lint_file}', id='flake8-config-exists'),
    pytest.param(False, flake8, 'flake8  {lint_file}', id='flake8-config-do-not-exists')
    # pylint: enable=line-too-long
))
def test_compare_with_main_branch(config_exists: bool,
                                  implementation: ModuleType,
                                  expect_command: str):
    with \
            mock.patch.object(implementation.Path, "exists", return_value=config_exists), \
            mock.patch.object(
                target=implementation.generics,
                attribute="lint_compare_with_main_branch"
            ) as lint_compare_with_main_branch:

        list(implementation.compare_with_main_branch())

        lint_compare_with_main_branch.assert_called_with(
            execute_command=expect_command,
            filters=(implementation._filter,)
        )
