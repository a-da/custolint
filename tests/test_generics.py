import re
from typing import Any, Callable, Sequence
from unittest import mock

import pytest

from custolint import generics, typing


def test_lint_compare_with_main_branch_no_python_files_in_changes():
    with mock.patch.object(generics.git, "changes"):
        assert not list(generics.lint_compare_with_main_branch(
            execute_command='pylint or flake8',
            filters=tuple()
        ))


def test_lint_compare_with_main_branch_with_python_files_in_changes(patch_bash: Callable):
    with \
            patch_bash(
                stdout="""
                ************* Module custolint.pylint
                src/custolint/pylint.py:35:0: C0301: Line too long (111/100) (line-too-long)
                ************* Module custolint.generics
                src/custolint/generics.py:79:9: W0511: TODO add parser (fixme)
                ************* Module custolint.b
                src/custolint/b.py:79:9: W0511: TODO add second parser (fixme)

                ------------------------------------------------------------------
                Your code has been rated at 9.95/10 (previous run: 9.92/10, +0.03)
                """
            ), \
            mock.patch.object(generics.git, "changes", return_value={
                'src/custolint/pylint.py': {
                    35: {
                        'email': 'a@b.c',
                        'date': 'today'
                    }
                },
                'src/custolint/generics.py': {
                    79: {
                        'email': 'a@b.c',
                        'date': 'today'
                    }
                },
            }):

        def my_dummy_test_filter(*args, **kwargs) -> bool:
            del args, kwargs
            return True

        assert list(generics.lint_compare_with_main_branch(
            execute_command='pylint',
            filters=(my_dummy_test_filter, )
        )) == [
            my_dummy_test_filter,
            typing.Lint(
                file_name='src/custolint/pylint.py',
                line_number=35,
                message='0: C0301: Line too long (111/100) (line-too-long)',
                email='a@b.c',
                date='today'
            ),
            typing.Lint(
                file_name='src/custolint/generics.py',
                line_number=79,
                message='9: W0511: TODO add parser (fixme)',
                email='a@b.c',
                date='today'
            )
        ]


def test_lint_compare_with_main_branch_similarity(patch_bash: Callable):
    with \
            patch_bash(
                stdout="""
                ************* Module custolint.pylint
                src/custolint/pylint.py:35:0: XXXX: Similar lines in
                line 1
                line 2
                """
            ), \
            mock.patch.object(generics.git, "changes", return_value={
                'src/custolint/pylint.py': {
                    35: {
                        'email': 'a@b.c',
                        'date': 'today'
                    }
                },
            }):

        def my_dummy_test_filter(*args, **kwargs) -> bool:
            del args, kwargs
            return True

        assert list(generics.lint_compare_with_main_branch(
            execute_command='pylint',
            filters=(my_dummy_test_filter, )
        )) == [
            my_dummy_test_filter,
            typing.Lint(
                file_name='src/custolint/pylint.py',
                line_number=35,
                message='0: XXXX: Similar lines in',
                email='a@b.c',
                date='today'
            )
        ]


def test_lint_compare_with_main_branch_lint_command_error(patch_bash: Callable, caplog):
    with \
            patch_bash(
                stderr='some lint error',
                code=1
            ), \
            mock.patch.object(generics.git, "changes", return_value={
                'src/custolint/pylint.py': None,
            }),\
            pytest.raises(SystemExit):

        list(generics.lint_compare_with_main_branch(
            execute_command='pylint',
            filters=tuple(),
        ))
    assert caplog.messages == ['Lint command failed: some lint error']


@pytest.mark.parametrize('to_output', (
    'print',
    'log',
))
def test_output(to_output: str):
    with mock.patch('builtins.print') as mocked:
        msg = 'some message'
        generics.output(
            msg=msg,
            log=mocked if to_output == 'log' else None
        )

    if to_output == 'log':
        mocked.info.assert_called_with(msg)
    else:
        mocked.assert_called_with(msg)


@pytest.mark.parametrize('linter_msg, parsed_as', (
    pytest.param(
        'a.py:35:4: W0104: Statement ... effect (pointless-statement)',
        ('a.py', 35, '4: W0104: Statement ... effect (pointless-statement)'),
        id='pylint'),
    pytest.param(
        "a.py:35:4: F401 'logging' imported but unused",
        ('a.py', 35, "4: F401 'logging' imported but unused"),
        id='flake8'),
    pytest.param(
        'a.py:35: error: Missing type .. type "Callable"  [type-arg]',
        ('a.py', 35, ' error: Missing type .. type "Callable"  [type-arg]'),
        id='mypy'),
))
def test_parse_message_lint(linter_msg: str, parsed_as: Sequence[Any]):
    assert generics._parse_message_line(linter_msg) == parsed_as


def test_parse_message_fail_to_parse():
    with pytest.raises(RuntimeError, match=re.escape(
        "Can not parse lint line 'Found 16 errors in 4 files (checked 9 source files)'"
    )):
        generics._parse_message_line(
            'Found 16 errors in 4 files (checked 9 source files)'
        )


def test_filter_output_has_found_something():
    with pytest.raises(SystemExit, match='41'):
        generics.filer_output(
            [
                typing.Lint(
                    file_name="file_name",
                    line_number=1,
                    message="message",
                    date='today',
                    email='email'
                ),
            ]
        )


def test_filter_output_with_true_filter():
    def my_dummy_test_filter(*args, **kwargs) -> bool:
        del args, kwargs
        return True

    with mock.patch.object(generics, 'output') as output:
        generics.filer_output(
            [
                my_dummy_test_filter,
                typing.Lint(
                    file_name="file_name",
                    line_number=1,
                    message="message",
                    date='today',
                    email='email'
                ),
                typing.Lint(
                    file_name="file_name",
                    line_number=1,
                    message="message",
                    date='today',
                    email='true.contributor'
                ),
                typing.Lint(
                    file_name="file_name",
                    line_number=1,
                    message="message",
                    date='today',
                    email='false.contributor'
                ),
            ],
            contributors=['true.contributor'],
            skip_contributors=['false.contributor']
        )

    output.assert_called_with('::Dry and Clean::')


def test_filter_output_with_false_filter():
    def my_dummy_test_filter(*args, **kwargs) -> bool:
        del args, kwargs
        return False

    with pytest.raises(SystemExit, match='41'):
        generics.filer_output(
            [
                my_dummy_test_filter,
                typing.Lint(
                    file_name="file_name",
                    line_number=1,
                    message="message",
                    date='today',
                    email='email'
                ),
            ]
        )


@pytest.mark.parametrize('kwargs, expect', (
    pytest.param({}, [
        mock.call('%s:%d %s ## %s:%s', 'file_name1', 1, 'message', 'not.in.contributor', 'today'),
        mock.call('%s:%d %s ## %s:%s', 'file_name2', 1, 'message', 'true.contributor', 'today'),
        mock.call('%s:%d %s ## %s:%s', 'file_name3', 1, 'message', 'false.contributor', 'today')
    ]),
    pytest.param({'contributors': ['true.contributor']}, [
        mock.call('%s:%d %s ## %s:%s', 'file_name2', 1, 'message', 'true.contributor', 'today'),
    ]),
    pytest.param({'skip_contributors': ['false.contributor']}, [
        mock.call('%s:%d %s ## %s:%s', 'file_name1', 1, 'message', 'not.in.contributor', 'today'),
        mock.call('%s:%d %s ## %s:%s', 'file_name2', 1, 'message', 'true.contributor', 'today'),
    ]),
    pytest.param(
        {
            'contributors': ['true.contributor'],
            'skip_contributors': ['false.contributor']
        },
        [
            mock.call('%s:%d %s ## %s:%s', 'file_name2', 1, 'message', 'true.contributor', 'today'),
        ]
    ),
))
def test_filter_output_with_contributors(kwargs, expect):
    with \
            mock.patch.object(generics, 'output') as output, \
            pytest.raises(SystemExit, match='41'):

        generics.filer_output(
            [
                typing.Lint(
                    file_name="file_name1",
                    line_number=1,
                    message="message",
                    date='today',
                    email='not.in.contributor'
                ),
                typing.Lint(
                    file_name="file_name2",
                    line_number=1,
                    message="message",
                    date='today',
                    email='true.contributor'
                ),
                typing.Lint(
                    file_name="file_name3",
                    line_number=1,
                    message="message",
                    date='today',
                    email='false.contributor'
                ),
            ],
            **kwargs
        )

    assert output.call_args_list == expect


@pytest.mark.parametrize('chunk,grouped', (
    pytest.param((1,), '1'),
    pytest.param((1, 2), '1-2'),
))
def test_output_grouping_by_email_and_file_name(chunk, grouped):
    contributor = typing.Contributor(
        email='a@b.c',
        date='today'
    )
    with mock.patch.object(generics, 'output') as output:
        generics._output_grouping_by_email_and_file_name(
            [
                typing.Coverage(
                    contributor=contributor,
                    file_name='a.py',
                    line_number=i
                ) for i in chunk
            ]
        )
        output.assert_called_with('%s:%s %05s %s', 'a.py', grouped, 'a@b.c', 'today')


def test_group_by_email_and_file_name_empty_log():
    with mock.patch.object(generics, 'output') as output:
        generics.group_by_email_and_file_name([])

        output.assert_called_with("::Dry and Clean::")


@pytest.mark.parametrize('log, expect_output', (
    pytest.param(
        [
            typing.Coverage(
                contributor=typing.Contributor(
                    email='a@b.c',
                    date='date'
                ),
                file_name='a.py',
                line_number=1,
            )
        ],
        [
            mock.call('%s:%s %05s %s', 'a.py', '1', 'a@b.c', 'date'),
        ]
    ),
    pytest.param(
        [
            typing.Coverage(
                contributor=typing.Contributor(
                    email='a@b.c',
                    date='date'
                ),
                file_name='a.py',
                line_number=i,
            ) for i in range(1, 5)
        ] + [
            typing.Coverage(
                contributor=typing.Contributor(
                    email='a@b.c',
                    date='date'
                ),
                file_name='b.py',
                line_number=1,
            )
        ],
        [
            mock.call('%s:%s %05s %s', 'a.py', '1-4', 'a@b.c', 'date'),
            mock.call('%s:%s %05s %s', 'b.py', '1', 'a@b.c', 'date')
        ]
    ),
))
def test_group_by_email_and_file_name_with_log(log: Sequence, expect_output: Sequence):
    with pytest.raises(SystemExit, match='41'), mock.patch.object(generics, 'output') as output:

        generics.group_by_email_and_file_name(log)

    assert output.call_args_list == expect_output
