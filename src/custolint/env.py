"""

Verbose mode
------------

Verbose mode with ``CUSTOLINT_LOG_LEVEL`` environment variable.

.. code-block:: bash

    # verbose mode
    $ CUSTOLINT_LOG_LEVEL=DEBUG custolint mypy
    [INFO] ...
    [DEBUG] additional information ...
    [WARNING] in case present

    # normal mode is INFO
    $ custolint mypy
    [INFO] ...

Git branch
----------

Override target branch with ``CUSTOLINT_MAIN_BRANCH`` environment variable.

.. code-block:: bash

    $ MAIN_BRANCH=JIRA-14407-core2-merge custolint mypy
    INFO:custolint.git:Compare current branch with 'main' branch
    INFO:custolint.git:Execute git diff command 'git diff origin/JIRA-14407-core2-merge -U0 --diff-filter=ACMRTUXB'
    INFO:custolint.git:Git diff detected 28 filed affected
    INFO:custolint.generics:Execute lint commands 'flake8 --config=config.d/.flake8 {lint_file}' for 18 files ...

    # The main branch is autodetected with ``git remote show origin`` command
    $ custolint flake8
    INFO:custolint.git:Compare current branch with 'main' branch
    INFO:custolint.git:Execute git diff command 'git diff origin/main -U0 --diff-filter=ACMRTUXB'
    INFO:custolint.git:Git diff detected 28 filed affected

Config.d
--------

Override config.d directory with ``CUSTOLINT_CONFIG_D`` environment variable.

.. versionadded:: 0.0.7

    .. code-block:: bash

        $ tree custolint.d
        custolint.d
        |-- mypy.ini
        |-- pylintrc
        `-- pylintrc.default.2.15.0

        $ CUSTOLINT_CONFIG_D=custolint.d custolint mypy


The configuration could be store into a different git repository

.. code-block:: bash

    $ git clone $GIT_SOME_REPO
    $ CUSTOLINT_CONFIG_D=$GIT_SOME_REPO/path/projectname/custolint.config.d custolint mypy

"""
import os

BRANCH_ENV = 'CUSTOLINT_MAIN_BRANCH'
CONFIG_D_ENV = 'CUSTOLINT_CONFIG_D'

LOG_LEVEL = os.getenv('CUSTOLINT_LOG_LEVEL') or "INFO"
BRANCH_NAME = os.getenv(BRANCH_ENV) or ""
CONFIG_D = os.getenv(CONFIG_D_ENV) or "config.d"
