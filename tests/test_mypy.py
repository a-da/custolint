from pathlib import Path
from typing import Any, Callable, Iterable, List, Optional, Sequence

import re
from unittest import mock

import pytest

from custolint import mypy, typing


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
        typing.Lint(
            file_name='b.py',
            line_number=42,
            message='message b',
            email='a@b.c',
            date='today'
        ),
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
    pytest.param(
        ['Success', ' no issues found in 2 source files'],
        None,
        id='skip-success'
    ),
))
def test_process_line_success(fields: Sequence[str], process_result: Optional[typing.Lint]):
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
            patch_bash(stdout='xxx'), \
            mock.patch.object(mypy.git, 'changes', return_value={}):
        assert not list(mypy.compare_with_main_branch())


def test_compare_with_main_branch_mypy_exception(patch_bash: Callable, caplog):
    with \
            patch_bash(stderr='Some exception', code=13), \
            mock.patch.object(mypy.git, 'changes', return_value={
                'a.py': {
                    1: 'contributor_a'
                }
            }), pytest.raises(SystemExit, match='13'):

        list(mypy.compare_with_main_branch())

    assert caplog.messages == ['Mypy command failed: Some exception']


@pytest.mark.parametrize('stdout, expect, process_line_return_value', (
    pytest.param("a.py:32: "
                 "error: Function is missing a return type annotation  "
                 "[no-untyped-def]",
                 [
                     'a.py',
                     '32',
                     ' error',
                     ' Function is missing a return type annotation  [no-untyped-def]'
                 ],
                 [[]],
                 id='match'),
    pytest.param("",
                 [''],
                 [[]],
                 id='no-match'),
    pytest.param("Found .* errors in .* file",
                 ["Found .* errors in .* file"],
                 None,
                 id='process-line-return-None'),
))
def test_compare_with_main_branch_some_files_affected(
    stdout: str,
    expect: Iterable[str],
    process_line_return_value: Optional[Iterable[str]],
    patch_bash: Callable[..., mock.Mock]
):

    with \
            patch_bash(stdout=stdout), \
            mock.patch.object(mypy.git, 'changes', return_value={
                'a.py': {
                    1: 'contributor_a'
                }
            }),\
            mock.patch.object(
                mypy,
                "_process_line",
                return_value=process_line_return_value
            ) as process_line:

        result = list(mypy.compare_with_main_branch())

        assert result == [
            mypy._filter,
            process_line.return_value
        ] if process_line.return_value else [
            mypy._filter
        ]

        process_line.assert_called_with(expect, {'a.py': {1: 'contributor_a'}})


@pytest.mark.parametrize('message, content, path, line_number', (
    pytest.param(
        'Some message [no-untyped-def]',
        ['def my_dummy_test_filter(*args, **kwargs) -> bool:'],
        Path('test_a.py'),
        1,
        id='dummy-functions-in-test-files'
    ),
    pytest.param(
        'Module has no attribute "git" [attr-defined]',
        [' mock.patch.object(generics.git, "changes"'],
        Path('test_a.py'),
        1,
        id='mock-transient-attribute'
    ),
    pytest.param(
        'Module has no attribute "git" [attr-defined]',
        [' mocker.patch.object(generics.git, "changes"'],
        Path('test_a.py'),
        1,
        id='mock-transient-attribute'
    ),
    pytest.param(
        'Module has no attribute "git" [attr-defined]',
        [
            ' mocker.patch.object(',
            '     generics.git, "changes" ...'
        ],
        Path('test_a.py'),
        2,
        id='mock-transient-attribute-multiline'
    ),
    pytest.param(
        'Some message [type-arg]',
        ['def test_a(name):'],
        Path('test_a.py'),
        1,
        id='type_arg'
    ),
    pytest.param(
        'Some message [no-untyped-def]',
        ['def test_a(name):'],
        Path('test_a.py'),
        1,
        id='no-untyped-def'
    ),
    pytest.param(
        'Some message [attr-defined]',
        ['def test_a(name):'],
        Path('test_a.py'),
        1,
        id='attr-defined'
    ),
    pytest.param(
        "Use \"-> None\" if function does not return a value",
        ['def test_a(name):'],
        Path('test_a.py'),
        1,
        id='return-none'
    ),
    pytest.param(
        "dict-item",
        ['def test_a(name):'],
        Path('test_a.py'),
        1,
        id='dict-item'
    ),
    pytest.param(
        "dict-item",
        ['def test_a(name):'],
        Path('test_a.py'),
        1,
        id='dict-item'
    ),
))
def test_filter_true_case(message: str, content: List[str], path: Path, line_number):
    assert mypy._filter(path, message, line_number, {
        path: content
    })


@pytest.mark.parametrize('message, content, path', (
    pytest.param(
        "Some message",
        ['def not_a_test_function(name):'],
        Path('not_a_test_file.py'),
        id='not-a-test-file'
    ),
    pytest.param(
        "Some message",
        ['def test_function(name):'],
        Path('test_file.py'),
        id='test-file-with_test-function'
    ),
    pytest.param(
        "Some message",
        ['def not_a_test_function(name):'],
        Path('test_file.py'),
        id='test-file-no-test-function'
    ),
))
def test_filter_false(message: str, content: List[str], path: Path):
    assert not mypy._filter(path, message, 1, {
        path: content
    })


@pytest.mark.parametrize('message, path_kwargs', (
    pytest.param(
        'Module has no attribute "git" [attr-defined]',
        {
            'name': 'test_not_a.py',
            'read_bytes.return_value': b' mock.patch.object(generics.git, "changes"'
        },
        id='mock-transient-attribute-no-cache'
    ),
))
def test_filter_true_not_cache(message: str, path_kwargs: Any, path_mock: mock.Mock):
    path = path_mock(**path_kwargs)
    # final_content =
    assert mypy._filter(path, message, 1, {})
