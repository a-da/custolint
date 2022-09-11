=========================
custolint - custom linter
=========================

.. make badges available https://docs.readthedocs.io/en/stable/badges.html

**Custolint** is a small library that help you
customize your existing code-validation pipeline.

.. | build-status | | docs | | coverage(100%) |

**Source Code**: `<https://github.com/a-da/custolint>`_.

Custolint implements:

- `Pylint <src/custolint/pylint.py>`_
- `Flake8 <src/custolint/flake8.py>`_
- `MyPy <src/custolint/mypy.py>`_
- `Python Coverage <src/custolint/coverage.py>`_


Motivation
----------

When you have a big old code base with thousands of lines, you can not just include a linter and enable 100% checks.

.. image:: https://www.meme-arsenal.com/memes/fb7dcfc4064d5b75e281d354590b13a5.jpg
  :width: 100
  :alt: You cannot just take and (Boromir meme)

Instead, you just enable 1% of the checks, which is very sad for a decent developer.

*Could you just enable to only check your changes ?*

**YES** you can,
please welcome **Custolint** - custom linter.

Idea
----

.. TODO: draw a diagram.

Given we have a project alike custolint, where we:

.. code-block:: bash

    $ tree
    .
    |-- config.d
    |   |-- mypy.ini
    |   `-- pylintrc
    |-- mypy.ini
    |-- pyproject.toml
    |-- setup.cfg
    |-- src
    |   |-- custolint
    |   |   |-- __init__.py
    |   |   |-- cli.py
    |   |   |-- coverage.py
    |   |   |-- flake8.py
    |   |   |-- generics.py --> added a new function ``custolint/generics.py:filer_output``
    |   |   |-- git.py  ---> changed a the function ``custolint/git.py:_blame``
    |   |   |-- mypy.py
    |   |   |-- pylint.py
    |   |   `-- typing.py
    |-- tests
    |   `-- test_custolint.py

When:

- We have to **detect affected files** with ``git diff`` and ``git blame``

  - ``custolint/git.py``
  - ``custolint/generics.py``

- **Run the linter** tool (pylint, flake8, mypy, coverage ...) with all available feature enables (the configuration have to be placed into  ``config.d/`` folder) only on changed affected files or parse log/result of the linter tool.

- **Match changed code** with the linters output, and consider only the match lines as failed lint criteria. It have to detect that ``custolint/generics.py:filer_output`` need unitest for coverage and ``custolint/git.py:_blame`` introduce a mypy typing issue.

Then:

- **Fail or Report** the build.

.. code-block:: bash

    $ coverage run --rcfile=config.d/.coveragerc -m pytest && \
        custolint coverage .coverage
    INFO:custolint.git:Execute git diff command 'git diff origin/main -U0 --diff-filter=ACMRTUXB'
    INFO:custolint.git:Git diff detected 16 filed affected
    INFO:custolint.coverage:execute coverage command: 'coverage report --data-file=.coverage --show-missing'
    src/custolint/git.py:66 not.committed.yet 2022-08-31

    $ custolint mypy
    INFO:custolint.mypy:MYPY COMPARE WITH 'main' branch
    INFO:custolint.git:Execute git diff command 'git diff origin/main -U0 --diff-filter=ACMRTUXB'
    INFO:custolint.git:Git diff detected 16 filed affected
    INFO:custolint.mypy:execute command 'mypy --config-file=config.d/mypy.ini @/var/folders/1l/592_sc0s3z1_19nmnr8v2zn00000gq/T/tmpi05fveqg'
    tests/test_custolint.py 31 Module has no attribute "bash"  [attr-defined] not.committed.yet 2022-08-31
    tests/test_custolint.py 125 Function is missing a return type annotation  [no-untyped-def] not.committed.yet 2022-08-31
    tests/test_custolint.py 140 Function is missing a return type annotation  [no-untyped-def] not.committed.yet 2022-08-31

Install
-------

From pip

.. code-block::

    $ make install
    pip install custolint
    Collecting custolint
      Downloading custolint-...-py3-none-any.whl (8.4 kB)
    Collecting bash...
    Installing collected packages: ...
    Successfully installed ... custolint-...

From GIT

.. code-block::

    git clone https://github.com/a-da/custolint.git

    # prod
    pip install .

    # dev
    pip install -e .[dev]


How to run:
-----------

.. code-block::

    cd "${YOUR_CODE}/"

    custolint mypy

    # code smell checking with pylint
    custolint pylint

    # code smell checking with flake8
    custolint flake8

    # 100% coverage checking for new commits
    coverage run --rcfile=config.d/.coveragerc -m pytest
    custolint coverage .coverage


Customisations:
---------------

Verbose mode with ``CUSTOLINT_LOG_LEVEL``.

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

Override target branch with ``CUSTOLINT_MAIN_BRANCH``.

.. code-block:: bash

    $ MAIN_BRANCH=JIRA-14407-core2-merge custolint mypy
    INFO:custolint.git:Compare current branch with 'main' branch
    INFO:custolint.git:Execute git diff command 'git diff origin/JIRA-14407-core2-merge -U0 --diff-filter=ACMRTUXB'
    INFO:custolint.git:Git diff detected 28 filed affected
    INFO:custolint.generics:Execute lint commands 'flake8 --config=config.d/.flake8 {lint_file}' for 18 files ...

    # The main branch is autodected with ``git remote show origin`` command
    $ custolint flake8
    INFO:custolint.git:Compare current branch with 'main' branch
    INFO:custolint.git:Execute git diff command 'git diff origin/main -U0 --diff-filter=ACMRTUXB'
    INFO:custolint.git:Git diff detected 28 filed affected

Exclude and/or include contributors with CLI ``--contributor`` argument.

.. code-block:: bash

    # TODO: not implemented yet
    custolint \
        --contributor=Josh,Andrei,Joanna \
        --skip-contributor=Ben \
            mypy

Halt on N messages.

.. code-block::

    # TODO: not implemented yet
    custolint --halt-on-N-messages=5 mypy

How to contribute:
------------------

For developers and contributors see the instruction here `<docs/for_developers.rst>`_.
