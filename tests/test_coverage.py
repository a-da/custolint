from typing import Callable, List

from unittest import mock

from custolint import coverage

import pytest


@pytest.mark.parametrize('missing, expect', (
    pytest.param(
        '1-3',
        [
            ('contributor_a', 'banana.py', 1),
            ('contributor_a', 'banana.py', 2),
            ('contributor_a', 'banana.py', 3),
        ],
        id='line-start-end'
    ),
    pytest.param(
        '3',
        [
            ('contributor_a', 'banana.py', 3),
        ],
        id='exact-line'
    ),
    pytest.param(
        '3000',
        [],
        id='no-line-in-git-changes'
    ),
    pytest.param(
        '1->exit',
        [
            ('contributor_a', 'banana.py', 1),
        ],
        id='exit'
    ),
    pytest.param(
        '1->3',
        [
            ('contributor_a', 'banana.py', 1),
        ],
        id='range->'
    ),
))
def test_process_missing_lines(missing: str, expect: List):
    assert list(coverage._process_missing_lines(
        file_name='banana.py',
        missing=missing,
        changes={
            'banana.py': {
                1: 'contributor_a',
                2: 'contributor_a',
                3: 'contributor_a'
            }
        }
    )) == expect


def test_compare_with_main_branch_with_missing(patch_bash: Callable):
    with \
            mock.patch.object(coverage.git, 'changes') as changes, \
            mock.patch.object(
                coverage,
                '_process_missing_lines',
                return_value=[1, 2, 3]
            ) as process_missing_lines,\
            patch_bash(stdout="""
        Name                        Stmts   Miss Branch BrPart  Cover   Missing
        -----------------------------------------------------------------------
        src/custolint/__init__.py       5      0      0      0   100%
        src/custolint/git.py           50      4     24      2    89%   25-26, 39-40
        tests/test_custolint.py        22      0      2      0   100%
        -----------------------------------------------------------------------
        TOTAL                          77      4     26      2    92%
    """):

        list(coverage.compare_with_main_branch('.coverage'))

        assert process_missing_lines.call_args_list == [
            mock.call(
                file_name='src/custolint/git.py',
                missing='25-26',
                changes=changes.return_value
            ),
            mock.call(
                file_name='src/custolint/git.py',
                missing='39-40',
                changes=changes.return_value
            )
        ]


def test_compare_with_main_branch_error(patch_bash: Callable, caplog):
    with \
            mock.patch.object(coverage.git, 'changes'), \
            patch_bash(stderr="some_error", code=1), \
            pytest.raises(SystemExit, match='1'):

        list(coverage.compare_with_main_branch('.coverage'))

    assert caplog.messages == ['Coverage command failed: some_error']
