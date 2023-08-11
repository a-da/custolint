"""
Prepare custom logging behaviour:
- when DEBUG include time and line code information
- include color log
"""
import logging
from logging import config

LEVEL_NAMES = (
    'CRITICAL',
    'FATAL',
    'ERROR',
    'WARNING',
    'INFO',
    'DEBUG',
    'NOTSET'
)


def setup(log_level: str, color_output: bool) -> None:
    """
    Configure the logging according to custolint features.

    .. important:: Should be invoked just once
    """

    value = logging._nameToLevel[log_level]  # noqa: private member # pylint: disable=protected-access

    prefix_formatter = 'debug_' if value <= logging.DEBUG else ''

    log_config = {
        "version": 1,
        "root": {
            "handlers": ["console"],
            "level": log_level,
            'propagate': 'no',
        },
        "handlers": {
            "console": {
                "formatter": prefix_formatter + ("colored" if color_output else "std_out"),
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
                # "format": "%(levelname)s: %(module)s : %(funcName)s: %(message)s",
                "format": "%(levelname)-8s:%(pathname)s:%(lineno)d: %(message)s",
                "datefmt": "%d-%m-%Y %I:%M:%S"
            },
            "debug_std_out": {
                "format": "%(levelname)-8s%(message)s",
                "datefmt": "%d-%m-%Y %I:%M:%S"
            },
            'colored': {
                '()': 'colorlog.ColoredFormatter',
                'format': "%(log_color)s%(levelname)-8s%(reset)s "
                          "%(blue)s%(message)s"
            },
            'debug_colored': {
                '()': 'colorlog.ColoredFormatter',
                'format': "%(log_color)s%(levelname)-8s%(reset)s "
                          "%(pathname)s:%(lineno)d %(blue)s%(message)s"
            }
        }
    }

    config.dictConfig(log_config)
