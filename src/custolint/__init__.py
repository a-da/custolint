import importlib.metadata
import logging
import os

logging.basicConfig(level=os.getenv('LOG_LEVEL') or logging.INFO)

VERSION = __version__ = importlib.metadata.version('custolint')
