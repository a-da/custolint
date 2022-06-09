Idea
====

1. Detect affected files

2. Run the tool with all available feature on only on changed affected files or parse log/result of the linter tool.

3. Match changed code with the linters output, and consider only the match lines as failed lint criteria.

4. Fail/Report the build.


Install
=======

From pip

.. code-block:: bash

    # TODO: not implemented yet
    pip install custolint

From repo

.. code-block:: bash

    git clone https://github.com/a-da/custolint.git
    pip install .

For development

.. code-block:: bash

    git clone https://github.com/a-da/custolint.git
    pip install -e .
    pip install -r requirements.dev

How to run:
===========

.. code-block:: bash

    cd "${YOUR_CODE}/"

    # typechecking with mypy implemented, set main branch, default is master
    # TODO: autodetect main branch
    MAIN_BRANCH=JIRA-14407-care2-merge python custolint mypy

    # code smell checking with pylint implemented
    custolint pylint

    # code smell checking with flake8 NOT implemented yet
    custolint flake8

    # 100% coverage checking for new commits NOT implemented yet
    pytest
    custolint coverage


Config filter

.. code-block:: bash

    # TODO: not implemented yet
    custolint \
        --contributor=Josh,Andrei,Joanna \
        --skip-contributor=Ben \
            mypy

Halt on N messages

.. code-block:: bash

    # TODO: not implemented yet
    custolint --halt-on-N-messages=5 mypy


How to develop:
===============

Run pytests

.. code-block:: bash

    cd "${CUSTOLINT_REPO}"
    pytest test_custolint.py
