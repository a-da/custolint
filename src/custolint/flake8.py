"""
=======================================================
`Flake8 <https://github.com/PyCQA/flake8>`_ integration
=======================================================

1. Find affected files

.. code-block:: bash

    $ git diff origin/main -U0 --diff-filter=ACMRTUXB
    INFO:custolint.git:Git diff detected 16 filed affected

2. Executing Flake8 linting only on affected file

.. command-output:: flake8 --config=config.d/.flake8 src/custolint/flake8.py
    :cwd: ..
    :returncode: 1

3. Filter all original Flake8 message with custolint rules

.. command-output:: custolint flake8
    :cwd: ..

"""
from typing import Dict, Iterator, Sequence, Union

from pathlib import Path

from . import _typing, env, generics
from .contributors import Contributors


# pylint: disable=unused-argument
def _filter(path: Path, message: str, line_number: int, cache: Dict[Path, Sequence[str]]) -> bool:
    """
    Return True if we want to skip the check else False if we want this check
    """
    return False
# pylint: enable=unused-argument


def compare_with_main_branch() -> Iterator[Union[_typing.Lint, _typing.FiltersType]]:
    """
    Compare all flake8 messages against code different to target branch.
    """
    config = Path(env.CONFIG_D, '.flake8')
    config_argument = f"--config={config}" if config.exists() else ""
    command = " ".join(("flake8", config_argument, "{lint_file}"))

    return generics.lint_compare_with_main_branch(
        execute_command=command,
        filters=(_filter,)
    )


def cli(contributors: Contributors, halt_on_n_messages: int, halt: bool = True) -> int:
    """Provide interface for flake8 CLI"""
    # pylint:disable=duplicate-code
    return generics.filer_output(
        log=compare_with_main_branch(),
        contributors=contributors,
        halt_on_n_messages=halt_on_n_messages,
        halt=halt
    )

