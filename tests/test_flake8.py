from custolint import flake8
from pathlib import Path

from custolint.contributors import Contributors
from custolint.generics import SYSTEM_EXIT_CODE_DRY_AND_CLEAN


def test_filter():
    assert not flake8._filter(
        path=Path(__file__),
        message='some-message',
        line_number=1,
        cache={}
    )


def test_cli(non_existing_white: Contributors):
    assert flake8.cli(non_existing_white, 0, False) == SYSTEM_EXIT_CODE_DRY_AND_CLEAN
