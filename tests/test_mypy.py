from typing import Callable

import re
from unittest import mock

from custolint import mypy

import pytest


def test_process_line_error():
    with pytest.raises(ValueError, match=re.escape('[]')):
        mypy._process_line([], {})


@pytest.mark.parametrize('fields, process_result', (
    pytest.param(
        ['a.py', '2', 'level', 'message a'],
        None,
        id='no-contributor'
    ),
    pytest.param(
        ['b.py', '42', 'level', 'message b'],
        ('b.py', 42, 'message b', 'a@b.c', 'today'),
        id='with-contributor'
    ),
    pytest.param(
        ['Found 6 errors in 1 file'],
        None,
        id='skip-summary'
    ),
    pytest.param(
        [''],
        None,
        id='skip-empty-lines'
    ),
))
def test_process_line(fields, process_result):
    assert mypy._process_line(fields, {
        'b.py': {
            42: {
                'email': 'a@b.c',
                'date': 'today'
            }
        }
    }) == process_result


def test_compare_with_main_branch_no_file_affected(patch_bash: Callable):
    with \
            patch_bash(stdout='''xxx'''), \
            mock.patch.object(mypy.git, 'changes', return_value={}):
        assert not list(mypy.compare_with_main_branch())


def test_compare_with_main_branch_some_files_affected(patch_bash: Callable):
    with \
            patch_bash(stdout="a.py:32: "
                              "error: Function is missing a return type annotation  "
                              "[no-untyped-def]"), \
            mock.patch.object(mypy.git, 'changes', return_value={
                'a.py': {
                    1: 'contributor_a'
                }
            }),\
            mock.patch.object(mypy, "_process_line") as process_line:

        assert list(mypy.compare_with_main_branch()) == [
            mypy._filter,
            process_line.return_value
        ]
        process_line.assert_called_with(
            [
                'a.py',
                '32',
                ' error',
                ' Function is missing a return type annotation  [no-untyped-def]'
            ],
            {'a.py': {1: 'contributor_a'}}
        )
