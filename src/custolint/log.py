"""
Prepare custom logging behaviour:
- when DEBUG include time and line code information
- include color log
"""
from typing import Optional

from logging import config

_CALLED_JUST_ONCE = True

LEVEL_NAMES = (
    'CRITICAL',
    'FATAL',
    'ERROR',
    'WARNING',
    'INFO',
    'DEBUG',
    'NOTSET'
)


def setup(log_level: Optional[str]) -> None:
    """
    Configure the logging according to custolint features.
    """
    global _CALLED_JUST_ONCE  # pylint: disable=global-statement

    if not _CALLED_JUST_ONCE:
        raise NotImplementedError('Expect log.count to be called just once')

    log_config = {
        "version": 1,
        "root": {
            "handlers": ["console"],
            "level": log_level,
            'propagate': 'no',
        },
        "handlers": {
            "console": {
                "formatter": "colored",
                "class": "logging.StreamHandler",
                "level": log_level
            }
        },
        'loggers': {
            'custolint': {
                'handlers': ['console'],
                'propagate': False,
            }
        },
        "formatters": {
            "std_out": {
                "format": "%(levelname)s: %(module)s : %(funcName)s: %(message)s",
                "datefmt": "%d-%m-%Y %I:%M:%S"
            },
            'colored': {
                '()': 'colorlog.ColoredFormatter',
                'format': "%(log_color)s%(levelname)-8s%(reset)s %(blue)s%(message)s"
            }
        }
    }

    config.dictConfig(log_config)
    _CALLED_JUST_ONCE = False
