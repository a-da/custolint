=========================
custolint - custom linter
=========================

|Custolint Logo|

.. make badges available https://docs.readthedocs.io/en/stable/badges.html

**Custolint** is a small library that help you to
customize your existing code-validation pipeline.

|Documentation| |Python Code Coverage| |License|

.. | docs | | coverage(100%) |

**Source Code**: `<https://github.com/a-da/custolint>`_.

Custolint implements:

- `Pylint <src/custolint/pylint.py>`_
- `Flake8 <src/custolint/flake8.py>`_
- `MyPy <src/custolint/mypy.py>`_
- `Python Coverage <src/custolint/coverage.py>`_


Motivation
----------

When you have a big old code base with thousands of lines, you can not just include a linter and enable 100% checks.

|Boromir Meme|

Instead, you just enable a tiny 1% of the checks, which is very disappointing for a decent developer.

*You could enable those 100% check just for your your changes with "custolint"*.

Idea
----

.. TODO: draw a diagram.

Given we have a project alike custolint, where we:

1. added a function ``custolint/generics.py:filer_output``.
2. changed a the function ``custolint/git.py:_blame``

.. code-block:: bash
    :name: given example

    $ tree
    ...
    |-- src
    |   |-- custolint
    ...
    |   |   |-- generics.py <<<< 1
    |   |   |-- git.py      <<<< 2
    |   |   |-- mypy.py
    |   |   |-- pylint.py
    |   |   `-- typing.py
    |-- tests
    |   `-- test_custolint.py
    ...

When:

- **Detect affected files** with ``git diff`` and ``git blame``

  - ``custolint/git.py``
  - ``custolint/generics.py``

- **Run the linter** tool (pylint, flake8, mypy, coverage ...) with all available feature enables (the configuration have to be placed into  ``config.d/`` folder) only on changed affected files or parse log/result of the linter tool.

- **Match changed code** with the linters output, and consider only the match lines as failed lint criteria. It has to detect that ``custolint/generics.py:filer_output`` need unitest for coverage and ``custolint/git.py:_blame`` introduce a mypy typing issue.

Then:

- **Fail or Report** the build.

.. code-block:: bash

    $ coverage run --rcfile=config.d/.coveragerc -m pytest && \
        custolint coverage config.d/.coveragerc
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

    # check typing
    custolint mypy

    # code smell checking with pylint
    custolint pylint

    # code smell checking with flake8
    custolint flake8

    # 100% coverage checking for new commits
    coverage run --rcfile=config.d/.coveragerc -m pytest
    custolint coverage config.d/.coverage



How to contribute:
------------------

For developers and contributors, see the instruction here `<docs/for_developers.rst>`_.


.. |Boromir Meme| image:: ./docs/_static/Boromir-meme.jpg
  :align: top
  :width: 100
  :alt: You cannot just take and (Boromir meme)

.. |Custolint Logo| image:: ./docs/_static/custolint-logo-the-future-by-RAP-studio.png
  :align: top
  :target: https://github.com/a-da/custolint
  :alt: Custolint logo

.. |Python Code Coverage| image:: https://codecov.io/gh/devanshshukla99/pytest-intercept-remote/branch/main/graph/badge.svg?token=81U29FC82V
    :alt: Python Code Coverage

.. |License| image:: https://img.shields.io/badge/License-MIT-yellow.svg
    :target: license.html
    :alt: License

.. |Documentation| image:: https://img.shields.io/readthedocs/custolint.svg
    :target: https://custolint.readthedocs.io/en/latest/
    :alt: Documentation
