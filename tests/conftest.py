from typing import Callable, Generator, Iterator

import os
import textwrap
from pathlib import Path
from unittest import mock

import bash
import pytest


@pytest.fixture(autouse=True, scope='session')
def cd_into_root() -> Generator[None, None, None]:
    """
    Change directory into the root directory
    """
    previous_cwd = os.getcwd()
    os.chdir(Path(__file__).parent.parent)

    yield

    os.chdir(previous_cwd)


def patch_bash(stdout: str = '', stderr: str = '', code: int = 0):
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
def fixture_path_bash() -> Iterator[Callable]:
    """
    fixture to patch ``bash.bash`` call
    """
    yield patch_bash
