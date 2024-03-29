from typing import Any, Callable, Iterator, Optional

import os
import textwrap
from pathlib import Path
from unittest import mock

import bash
import pytest

from custolint.contributors import Contributors
from custolint import git


@pytest.fixture(autouse=True, scope='session')
def cd_into_root() -> Iterator[None]:
    """
    Change directory into the root directory
    """
    previous_cwd = os.getcwd()
    os.chdir(Path(__file__).parent.parent)

    yield

    os.chdir(previous_cwd)


def patch_bash(stdout: Optional[str] = '',
               stderr: Optional[str] = '',
               code: Optional[int] = 0) -> mock.MagicMock:
    """
    Wrapper for patching bash library, to be used by py:func:`.fixture_path_bash`
    """
    return mock.patch.object(
        target=bash,
        attribute="bash",
        side_effect=[
            mock.Mock(
                stdout=textwrap.dedent(stdout).encode(),
                stderr=textwrap.dedent(stderr).encode(),
                code=code
            )
        ]
    )


@pytest.fixture(name='patch_bash')
def fixture_path_bash() -> Iterator[Callable[..., mock.Mock]]:
    """
    fixture to patch ``bash.bash`` call
    """
    yield patch_bash


@pytest.fixture(name='path_mock')
def _path_mock() -> Callable[..., mock.Mock]:
    def _(name: str, **kwargs: Any) -> mock.Mock:
        path = mock.Mock(**kwargs)
        path.name = name
        return path

    return _


@pytest.fixture(scope='module', name='contributors')
def _contributors() -> Contributors:
    return Contributors.from_cli('', '')


@pytest.fixture(scope='module')
def non_existing_white() -> Contributors:
    """
    A contributors which not exists
    """
    return Contributors.from_cli('non-existing-white', '')


@pytest.fixture
def _autodetect() -> mock.Mock:
    return mock.patch.object(  # type: ignore[return-value]
        target=git,
        attribute=git._autodetect.__qualname__,
        return_value=(Path('/path/to/git'), "main")
    )
