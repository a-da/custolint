"""
... Put here some global configuration or variables.

:py:const:`custolint.VERSION` or :py:const:`custolint.__version__`:
    Current version of "custolint" library.
"""
import importlib.metadata
import logging

from . import env

logging.basicConfig(level=env.LOG_LEVEL)

VERSION = __version__ = importlib.metadata.version('custolint')
