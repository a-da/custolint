from unittest import mock

from custolint import generics


def test_lint_compare_with_main_branch():
    with mock.patch.object(generics.git, "changes"):
        list(generics.lint_compare_with_main_branch(
            execute_command='pylint or flake8',
            filters=tuple()
        ))
