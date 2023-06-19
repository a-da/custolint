import re
from typing import Any, Callable, Sequence
from unittest import mock

import pytest

from custolint import generics, typing
from custolint.contributors import Contributors


@pytest.fixture(scope='module', name='contributors')
def _contributors() -> Contributors:
    return Contributors.from_cli('', '')


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
                        'date': 'today',
                        'author': 'John Snow'
                    }
                },
                'src/custolint/generics.py': {
                    79: {
                        'email': 'a@b.c',
                        'date': 'today',
                        'author': 'John Snow'
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
                author='John Snow',
                file_name='src/custolint/pylint.py',
                line_number=35,
                message='0: C0301: Line too long (111/100) (line-too-long)',
                email='a@b.c',
                date='today'
            ),
            typing.Lint(
                author='John Snow',
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
                        'date': 'today',
                        'author': 'John Snow'
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
                author='John Snow',
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


@pytest.mark.parametrize("error_code, halt_on_n_messages", (
    pytest.param(generics.SYSTEM_EXIT_CODE_WITH_ALL_MESSAGES_INCLUDED, 0, id='halt_on_0_messages'),
    pytest.param(generics.SYSTEM_EXIT_CODE_WITH_HALT_ON_N_MESSAGES, 2, id='halt_on_2_messages'),
))
def test_filter_output_has_found_something(
        error_code: int,
        halt_on_n_messages: int,
        contributors: Contributors):
    with pytest.raises(SystemExit, match=str(error_code)):
        generics.filer_output(
            log=[
                typing.Lint(
                    author='John Snow',
                    file_name="file_name",
                    line_number=i,
                    message="message",
                    date='today',
                    email='email'
                ) for i in range(1, 5)

            ],
            contributors=contributors,
            halt_on_n_messages=halt_on_n_messages
        )


def test_filter_output_with_true_filter():
    def my_dummy_test_filter(*args, **kwargs) -> bool:
        del args, kwargs
        return True

    with mock.patch.object(generics, 'output') as output:
        generics.filer_output(
            log=[
                my_dummy_test_filter,
                typing.Lint(
                    author='John Snow',
                    file_name="file_name",
                    line_number=1,
                    message="message",
                    date='today',
                    email='email'
                ),
                typing.Lint(
                    author='John Snow',
                    file_name="file_name",
                    line_number=1,
                    message="message",
                    date='today',
                    email='true.contributor'
                ),
                typing.Lint(
                    author='John Snow',
                    file_name="file_name",
                    line_number=1,
                    message="message",
                    date='today',
                    email='false.contributor'
                ),
            ],
            contributors=Contributors.from_cli('true.contributor', ''),
            halt_on_n_messages=0
        )

    output.assert_called_with('::Dry and Clean::')


def test_filter_output_with_false_filter(contributors: Contributors):
    def my_dummy_test_filter(*args, **kwargs) -> bool:
        del args, kwargs
        return False

    with pytest.raises(SystemExit, match=str(generics.SYSTEM_EXIT_CODE_WITH_ALL_MESSAGES_INCLUDED)):
        generics.filer_output(
            log=[
                my_dummy_test_filter,
                typing.Lint(
                    author='John Snow',
                    file_name="file_name",
                    line_number=1,
                    message="message",
                    date='today',
                    email='email'
                ),
            ],
            contributors=contributors,
            halt_on_n_messages=0
        )


@pytest.mark.parametrize('white, black, expect', (
    pytest.param(
        '',
        '',
        [
            mock.call(
                '%s:%d %s ## %s:%s',
                'file_name1',
                1,
                'message',
                'not.in.contributor',
                'today'
            ),
            mock.call(
                '%s:%d %s ## %s:%s',
                'file_name2',
                1,
                'message',
                'true.contributor',
                'today'
            ),
            mock.call(
                '%s:%d %s ## %s:%s',
                'file_name3',
                1,
                'message',
                'false.contributor',
                'today'
            )
        ],
        id='no-contributors'
    ),
    pytest.param(
        '',
        'false.contributor',
        [
            mock.call(
                '%s:%d %s ## %s:%s',
                'file_name1', 1,
                'message',
                'not.in.contributor',
                'today'
            ),
            mock.call(
                '%s:%d %s ## %s:%s',
                'file_name2',
                1,
                'message',
                'true.contributor',
                'today'
            ),
        ],
        id='exclude-contributors'
    ),
    pytest.param(
        'true.contributor',
        '',
        [
            mock.call(
                '%s:%d %s ## %s:%s',
                'file_name2',
                1,
                'message',
                'true.contributor',
                'today'
            ),
        ],
        id='include-contributors'
    ),
))
def test_filter_output_with_contributors(white: str, black: str, expect: Sequence):
    contributors = Contributors.from_cli(white, black)

    with \
            mock.patch.object(generics, 'output') as output, \
            pytest.raises(SystemExit,
                          match=str(generics.SYSTEM_EXIT_CODE_WITH_ALL_MESSAGES_INCLUDED)):

        generics.filer_output(
            log=[
                typing.Lint(
                    author='John Snow',
                    file_name="file_name1",
                    line_number=1,
                    message="message",
                    date='today',
                    email='not.in.contributor'
                ),
                typing.Lint(
                    author='John Snow',
                    file_name="file_name2",
                    line_number=1,
                    message="message",
                    date='today',
                    email='true.contributor'
                ),
                typing.Lint(
                    author='John Snow',
                    file_name="file_name3",
                    line_number=1,
                    message="message",
                    date='today',
                    email='false.contributor'
                ),
            ],
            contributors=contributors,
            halt_on_n_messages=0
        )

    assert output.call_args_list == expect


def test_filter_output_with_contributors_black_and_white():
    with pytest.raises(ValueError,
                       match='Mutually exclusion for ``white`` and ``black`` arguments'):
        Contributors.from_cli('white', 'black')


@pytest.mark.parametrize('chunk,grouped', (
    pytest.param((1,), '1'),
    pytest.param((1, 2), '1-2'),
))
def test_output_grouping_by_email_and_file_name(chunk, grouped):
    contributor = typing.Contributor(
        author='John Snow',
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


def test_group_by_email_and_file_name_empty_log(contributors: Contributors):
    with mock.patch.object(generics, 'output') as output:
        generics.group_by_email_and_file_name(
            log=[],
            contributors=contributors,
            halt_on_n_messages=0)

        output.assert_called_with("::Dry and Clean::")


@pytest.mark.parametrize('log, halt_on_n_messages, expect_output', (
    pytest.param(
        [
            typing.Coverage(
                contributor=typing.Contributor(
                    author='John Snow',
                    email='a@b.c',
                    date='date'
                ),
                file_name='a.py',
                line_number=1,
            )
        ],
        0,
        [
            mock.call('%s:%s %05s %s', 'a.py', '1', 'a@b.c', 'date'),
        ],
        id='single-line'
    ),
    pytest.param(
        [
            typing.Coverage(
                contributor=typing.Contributor(
                    author='John Snow',
                    email='a@b.c',
                    date='date'
                ),
                file_name='a.py',
                line_number=i,
            ) for i in range(1, 5)
        ] + [
            typing.Coverage(
                contributor=typing.Contributor(
                    author='John Snow',
                    email='a@b.c',
                    date='date'
                ),
                file_name='b.py',
                line_number=1,
            )
        ],
        0,
        [
            mock.call('%s:%s %05s %s', 'a.py', '1-4', 'a@b.c', 'date'),
            mock.call('%s:%s %05s %s', 'b.py', '1', 'a@b.c', 'date')
        ],
        id='two-files'
    ),
    pytest.param(
        [
            typing.Coverage(
                contributor=typing.Contributor(
                    author='John Snow',
                    email='a@b.c',
                    date='date'
                ),
                file_name='a.py',
                line_number=i,
            ) for i in range(1, 5)
        ],
        2,
        [
            mock.call('%s:%s %05s %s', 'a.py', '1-2', 'a@b.c', 'date'),
        ],
        id='halt-on-2-messages'
    ),
    pytest.param(
        [
            typing.Coverage(
                contributor=typing.Contributor(
                    author='John Snow',
                    email='a@b.c',
                    date='date'
                ),
                file_name='a.py',
                line_number=1,
            ),
            typing.Coverage(
                contributor=typing.Contributor(
                    author='Tony Stark',
                    email='a@b.c',
                    date='date'
                ),
                file_name='a.py',
                line_number=2,
            )
        ],
        0,
        [
            mock.call('%s:%s %05s %s', 'a.py', '1', 'a@b.c', 'date')
        ],
        id='only-john-snow-contributor-name'
    ),
))
def test_group_by_email_and_file_name_with_log(
        log: Sequence[typing.Coverage],
        halt_on_n_messages: int,
        expect_output: Sequence[str]):

    error_code = (
        generics.SYSTEM_EXIT_CODE_WITH_ALL_MESSAGES_INCLUDED
        if not halt_on_n_messages else generics.SYSTEM_EXIT_CODE_WITH_HALT_ON_N_MESSAGES
    )
    with \
            pytest.raises(SystemExit, match=str(error_code)), \
            mock.patch.object(generics, 'output') as output:

        generics.group_by_email_and_file_name(
            log=log,
            contributors=Contributors.from_cli('John Snow', ""),
            halt_on_n_messages=halt_on_n_messages
        )

    assert output.call_args_list == expect_output
