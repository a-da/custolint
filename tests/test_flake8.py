from custolint import flake8
from pathlib import Path


def test_filter():
    assert not flake8._filter(
        path=Path(__file__),
        message='some-message',
        line_number=1,
        cache={}
    )
