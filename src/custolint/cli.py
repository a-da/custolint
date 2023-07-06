# pragma: no cover this module will not be covered by the tests,
# since it is using most of ``click`` external already tested API
"""
Command line interface API based on python click library
"""
from typing import Any, Callable, Dict, Tuple

import functools
import logging
import sys
from configparser import ConfigParser
from pathlib import Path

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

    @click.option('--halt', envvar='CUSTOLINT_HALT', default=True, type=bool)
    @click.option('--color-output', envvar='CUSTOLINT_COLOR_OUTPUT', default=True, type=bool)
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
                color_output: bool,
                **kwargs: Any) -> Any:
        try:
            _contributors = Contributors.from_cli(contributors, skip_contributors)
        except ValueError as value_error:
            raise click.UsageError('Mutually exclusion for arguments '
                                   '--skip-contributors and --contributor') from value_error

        log.setup(
            log_level=log_level or env.LOG_LEVEL,
            color_output=color_output
        )
        LOG.info('---- %s ------', func_name)
        return func(_contributors, halt_on_n_messages, **kwargs)
    return wrapper


@common_params
def _mypy(contributors: Contributors, halt_on_n_messages: int, halt: bool) -> None:
    mypy.cli(
        contributors=contributors,
        halt_on_n_messages=halt_on_n_messages,
        halt=halt
    )


@common_params
def _pylint(contributors: Contributors, halt_on_n_messages: int, halt: bool) -> None:
    pylint.cli(
        contributors=contributors,
        halt_on_n_messages=halt_on_n_messages,
        halt=halt
    )


@common_params
def _flake8(contributors: Contributors, halt_on_n_messages: int, halt: bool) -> None:
    flake8.cli(
        contributors=contributors,
        halt_on_n_messages=halt_on_n_messages,
        halt=halt
    )


if coverage.coverage:
    @click.option('--data-file',
                  type=click.Path(exists=True),
                  default='.coverage',
                  help=coverage.coverage.cmdline.Opts.input_datafile.help)  # pylint: disable=no-member
    @common_params
    def _coverage(contributors: Contributors,
                  halt_on_n_messages: int,
                  halt: bool,
                  data_file: click.Path) -> None:
        coverage.cli(
            contributors=contributors,
            halt_on_n_messages=halt_on_n_messages,
            halt=halt,
            data_file=click.format_filename(data_file)  # type: ignore[arg-type]
        )


def _parse_cmd_array(value: str) -> Tuple[str, ...]:
    """
    >>> _parse_cmd_array('blue, red,green')
    ('blue', 'red', 'green')
    >>> _parse_cmd_array(' ')
    ()
    """
    return tuple(i.strip() for i in value.split(',') if i.strip())


def _parse_cmd_kwargs(value: str) -> Dict[str, str]:
    """
    >>> _parse_cmd_kwargs('data_file:.coverage,a:b')
    {'data_file': '.coverage', 'a': 'b'}
    >>> _parse_cmd_kwargs(',')
    {}
    """
    kwargs = {}
    for _v in _parse_cmd_array(value):
        key, value = _v.split(':')
        kwargs[key.strip()] = value.strip()

    return kwargs


@click.argument('config', type=click.Path(exists=True))
@common_params
def _from_config(contributors: Contributors,
                 halt_on_n_messages: int,
                 halt: bool,
                 config: click.Path) -> None:
    config_path = Path(config)  # type: ignore[arg-type]
    if config_path.name == 'setup.cfg':
        setup_cfg = ConfigParser()
        setup_cfg.read(config_path)
        commands = _parse_cmd_array(setup_cfg['tool:custolint']['commands'])
        halt = halt or setup_cfg['tool:custolint'].getboolean('halt')
        LOG.info('The following commands: %r will run with halt=%r', commands, halt)

        _globals = globals()

        halt_error_code = generics.SYSTEM_EXIT_CODE_DRY_AND_CLEAN
        for cmd in commands:
            try:
                cmd_kwargs_raw = setup_cfg['tool:custolint'][cmd + '_kwargs']
            except KeyError:
                LOG.warning('no %r command configuration, skip ...', cmd + '_kwargs')
                continue

            cmd_kwargs = _parse_cmd_kwargs(cmd_kwargs_raw)

            LOG.info('---- from_config:%s ------', cmd)

            return_code = getattr(_globals[cmd], 'cli')(
                contributors=contributors,
                halt_on_n_messages=halt_on_n_messages,
                halt=halt,
                **cmd_kwargs,
            )

            if return_code != generics.SYSTEM_EXIT_CODE_DRY_AND_CLEAN:
                halt_error_code = return_code

        sys.exit(halt_error_code)

    raise NotImplementedError(config_path.name)
