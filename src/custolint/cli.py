# pragma: no cover this module will not be covered by the tests,
# since it is using most of ``click`` external already tested API
"""
Command line interface API based on python click library
"""
from typing import Any, Callable

import functools
import logging

import click

from . import __version__, coverage, env, flake8, generics, log, mypy, pylint
from .contributors import Contributors

FuncType = Callable[..., None]
LOG = logging.getLogger(__name__)


@click.version_option(__version__)
@click.group()
def cli() -> None:
    """Another custom linter layer. See the commands bellow for supported layers."""


def common_params(func: FuncType) -> FuncType:
    """Share the same options across all commands"""
    func_name = func.__name__[1:]

    @click.option('--halt-on-N-messages',
                  default=0,
                  type=int,
                  help='Fast halt when reaching N messages. '
                       'Is taken in consideration only if greater the zero.')
    @click.option('--skip-contributors',
                  default='',
                  help='Exclude contributors by name or emails,'
                       'mutually exclusive with --contributors')
    @click.option('--contributors',
                  default='',
                  help='Include only contributors by name or emails,'
                       'mutually exclusive with --contributors')
    @click.option('--log-level', type=click.Choice(log.LEVEL_NAMES))
    @cli.command(name=func_name)
    @functools.wraps(func)
    def wrapper(log_level: str,
                contributors: str,
                skip_contributors: str,
                halt_on_n_messages: int,
                **kwargs: Any) -> Any:
        try:
            _contributors = Contributors.from_cli(contributors, skip_contributors)
        except ValueError as value_error:
            raise click.UsageError('Mutually exclusion for arguments '
                                   '--skip-contributors and --contributor') from value_error

        log.setup(log_level or env.LOG_LEVEL)
        LOG.info('---- %s ------', func_name)
        return func(_contributors, halt_on_n_messages, **kwargs)
    return wrapper


@common_params
def _mypy(contributors: Contributors, halt_on_n_messages: int) -> None:
    generics.filer_output(mypy.compare_with_main_branch(), contributors, halt_on_n_messages)


@common_params
def _pylint(contributors: Contributors, halt_on_n_messages: int) -> None:
    generics.filer_output(pylint.compare_with_main_branch(), contributors, halt_on_n_messages)


@common_params
def _flake8(contributors: Contributors, halt_on_n_messages: int) -> None:
    generics.filer_output(flake8.compare_with_main_branch(), contributors, halt_on_n_messages)


@click.option('--data-file',
              type=click.Path(exists=True),
              help="Read coverage data for report generation from this file. "
                   "Defaults to '.coverage'. [env: COVERAGE_FILE]")
@common_params
def _coverage(contributors: Contributors, halt_on_n_messages: int, data_file: click.Path) -> None:
    file_path = click.format_filename(data_file)  # type: ignore[arg-type]
    generics.group_by_email_and_file_name(
        log=coverage.compare_with_main_branch(file_path),
        contributors=contributors,
        halt_on_n_messages=halt_on_n_messages
    )
