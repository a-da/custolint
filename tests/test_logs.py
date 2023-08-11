from unittest import mock
import pytest

from custolint import log


@pytest.mark.parametrize('level', ('INFO', 'DEBUG'))
@pytest.mark.parametrize('color_output', (True, False))
def test_log_formatters(level, color_output):

    with mock.patch.object(log.config, log.config.dictConfig.__qualname__) as dict_config:
        log.setup(
            log_level=level,
            color_output=color_output
        )

    dict_config_arg = dict_config.call_args.args[0]
    formatter = dict_config_arg['handlers']['console']['formatter']

    format_ = dict_config_arg['formatters'][formatter]['format']

    assert format_ % {
        'log_color': ':RED:',
        'levelname': level,
        'reset': '.',
        'blue': ':BLUE:',
        'message': 'message',
        'pathname': '/custolint/src/file1.py',
        'lineno': 69
    }
