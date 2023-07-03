from typing import Optional

import pytest

from custolint import pylint
from pathlib import Path
from unittest import mock

from custolint.contributors import Contributors
from custolint.generics import SYSTEM_EXIT_CODE_DRY_AND_CLEAN


def path_mock(name: str, **kwargs):
    path = mock.Mock(**kwargs)
    path.name = name
    return path


PYLINT_PATH_MOCK = path_mock(name='src/custolint/pylint_cache.py')

BANANA_2_PATH_MOCK = path_mock(
    name='test_banana2.py',
    **{
        'read_bytes.return_value': b'def test_banana2():'
    }
)


@pytest.mark.parametrize('path, message', (
    (Path('tests/test_pylint.py'), 'some-message'),
    (Path('src/custolint/pylint.py'), 'some-message'),
    (Path('tests/conftest.py'), 'some-message'),
    pytest.param(
        path_mock(
            name='test_conf.py',
            **{
                'read_bytes.return_value': b'def test_banana1():'
            }
        ),
        'some-message1',
        id='not-in-cache'
    ),
    pytest.param(
        PYLINT_PATH_MOCK,
        'some-message',
        id='not-test-in-cache'
    ),
    pytest.param(
        path_mock(
            name='conftest.py',
            **{
                'read_bytes.return_value': b'def test_banana2():'
            }
        ),
        'some.message2',
        id='conftest'
    ),
    pytest.param(
        BANANA_2_PATH_MOCK,
        'some-message1',
        id='test-in-cache'
    ),
))
def test_filter_false(path: Path, message: str):
    assert not pylint._filter(
        path=path,
        message=message,
        line_number=1,
        cache={
            BANANA_2_PATH_MOCK: 'content-BANANA_2_PATH_MOCK',
            PYLINT_PATH_MOCK: ['content-PYLINT_PATH_MOCK'],
        }
    )


@pytest.mark.parametrize('message, line_content', (
    pytest.param('Some Message (missing-function-docstring)', b'def test_some_function():'),
    pytest.param('Some Message (missing-module-docstring)', b'def test_some_function():'),
    pytest.param('Some Message (protected-access)', b'def test_some_function():'),
    pytest.param('todo: space-1234: do that', b'def test_some_function():'),
    pytest.param('R0801: Similar lines in 1000 files', b'def test_some_function():'),
    pytest.param('Some Message (missing-function-docstring)', b'def mock_get_data(*_, **__):')
))
def test_filter_test_functions_true(message: str, line_content: bytes):
    assert pylint._filter(
        path=path_mock(
            name='test_conf.py',
            **{
                'read_bytes.return_value': line_content
            }
        ),
        message=message,
        line_number=1,
        cache={}
    )


@pytest.mark.parametrize('message, file_name, previous_line_content, line_content, is_filtered', (
    pytest.param(
        'Some Message (missing-function-docstring)',
        'not_test_module.py',
        None,
        'def filter_test_functions(',
        True,
        id='do-filter-missing-function-docstring'
    ),
    pytest.param(
        'Some Message (too-many-public-methods)',
        'test_module.py',
        None,
        'something',
        True,
        id='do-filter-too-many-public-methods'
    ),
    pytest.param(
        'Some Message (logging-fstring-interpolation)',
        'module.py',
        None,
        'log.info(f"{some_var}")',
        True,
        id='do-filter-logging-fstring-interpolation'
    ),
    pytest.param(
        'Some Message (logging-fstring-interpolation)',
        'module.py',
        None,
        'log.debug(f"{some_var}")',
        False,
        id='do-not-filter-logging-fstring-interpolation'
    ),
    pytest.param(
        'Some Message (missing-function-docstring)',
        'not_test_module.py',
        None,
        'def do_that(',
        False,
        id='do-not-filter'
    ),
    pytest.param(
        'Some Message (missing-function-docstring)',
        'not_test_module.py',
        "@property",
        'def radius(self):',
        True,
        id='filter-a-property'
    ),
    pytest.param(
        ' should have "self" as first argument (no-self-argument)',
        'not_test_module.py',
        "@validator('name')",
        "def name_must_contain_space(cls, v):",
        True,
        id='filter-pydantic-validation-method'
    ),
))
def test_filter_no_test_functions_true(message: str,
                                       file_name: str,
                                       previous_line_content: Optional[str],
                                       line_content: str,
                                       is_filtered: bool):
    assert pylint._filter(
        path=path_mock(
            name=file_name,
            **{
                'read_bytes.return_value': "\n".join((
                    (previous_line_content or ''),
                    line_content
                )).encode()
            }
        ),
        message=message,
        line_number=2,
        cache={}
    ) is is_filtered


def test_cli(non_existing_white: Contributors):
    assert pylint.cli(non_existing_white, 0, False) == SYSTEM_EXIT_CODE_DRY_AND_CLEAN
