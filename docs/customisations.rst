==============
Customisations
==============

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
    [WARNING] in case present

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

Contributor
-----------

Exclude and/or include contributors with CLI ``--contributor`` argument.

.. versionadded:: 0.0.7

    .. code-block:: bash

        # TODO: not implemented yet
        custolint \
            --contributor=Josh,Andrei,Joanna \
            --skip-contributor=Ben \
                mypy


Halt on N messages
------------------

.. versionadded:: 0.0.7

    .. code-block::

        # TODO: not implemented yet
        custolint --halt-on-N-messages=5 mypy
