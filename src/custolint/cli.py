# pragma: no cover this module will not be covered by the tests,
# since it is using most of ``click`` external already tested API
"""
Command line interface API
"""
import logging

import click

from . import coverage, flake8, generics, mypy, pylint, env, log

LOG = logging.getLogger(__name__)


@click.group()
def cli() -> None:
    """Another custom linter layer. See the commands bellow for supported layers."""

# TODO if there are no changed files stop all and inform about this
# TODO: in case of debug show the time in the log
# TODO: make a colored logs


@click.option('--log-level')
@cli.command(name='mypy')
def _mypy(log_level: str) -> None:
    log.setup(log_level or env.LOG_LEVEL)
    LOG.info('---- mypy ------')
    generics.filer_output(mypy.compare_with_main_branch())


@click.option('--log-level')
@cli.command(name='pylint')
def _pylint(log_level: str) -> None:
    log.setup(log_level or env.LOG_LEVEL)
    click.echo(click.style('---- pylint ------', fg='green'))
    generics.filer_output(pylint.compare_with_main_branch())


@click.option('--log-level')
@cli.command(name='flake8')
def _flake8(log_level: str) -> None:
    log.setup(log_level or env.LOG_LEVEL)
    click.echo(click.style('---- flake8 ------', fg='green'))
    generics.filer_output(flake8.compare_with_main_branch())


@click.option('--log-level')
@click.option('--data-file',
              help="Read coverage data for report generation from this file. "
                   "Defaults to '.coverage'. [env: COVERAGE_FILE]")
@cli.command(name='coverage')
def _coverage(data_file: str, log_level: str) -> None:
    log.setup(log_level or env.LOG_LEVEL)
    click.echo(click.style('---- coverage ------', fg='green'))

    coverage_file_location = data_file
    generics.group_by_email_and_file_name(
        coverage.compare_with_main_branch(coverage_file_location)
    )
