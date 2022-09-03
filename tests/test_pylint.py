import pytest

from custolint import pylint
from pathlib import Path
from unittest import mock


def path_mock(name: str, **kwargs):
    path = mock.Mock(**kwargs)
    path.name = name
    return path


PYLINT_PATH_MOCK = path_mock(name='src/custolint/pylint.py')

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
        id='in-cache'
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
            BANANA_2_PATH_MOCK: 'content-BANANA_2_PATH_MOCK'
        }
    )


@pytest.mark.parametrize('message', (
    'Some Message (missing-function-docstring)',
    'Some Message (missing-module-docstring)',
    'Some Message (protected-access)',
    'todo: space-1234: do that',
))
def test_filter_test_functions_true(message: str):
    assert pylint._filter(
        path=path_mock(
            name='test_conf.py',
            **{
                'read_bytes.return_value': b'def test_some_function():'
            }
        ),
        message=message,
        line_number=1,
        cache={}
    )
