=========================
custolint - custom linter
=========================

Motivation
==========

When you have a big old code base with thousands of lines, you can not just include a linter and enable 100% checks.

.. image:: https://www.meme-arsenal.com/memes/fb7dcfc4064d5b75e281d354590b13a5.jpg
  :width: 400
  :alt: You cannot just take and (Boromir meme)
  
Instead, you just enable 1% of the checks, which is very sad for a decent developer.

There is a better solution for this ! Welcome **custolint** - custom linter.

Idea
====

1. Detect affected files.

2. Run the tool with all available feature enables only on changed affected files or parse log/result of the linter tool.

3. Match changed code with the linters output, and consider only the match lines as failed lint criteria.

4. Fail or Report the build.


Install
=======

From pip

.. code-block:: bash

    $ make install
    pip install custolint
    Collecting custolint
      Downloading custolint-...-py3-none-any.whl (8.4 kB)
    Collecting bash...
    Installing collected packages: ...
    Successfully installed ... custolint-...

From repo

.. code-block:: bash

    git clone https://github.com/a-da/custolint.git

    # prod
    pip install .

    # dev
    pip install -e .[dev]

How to run:
===========

.. code-block:: bash

    cd "${YOUR_CODE}/"

    # when MAIN_BRANCH is develop
    python custolint mypy

    # typechecking with mypy implemented, set main branch, default is master
    # TODO: autodetect main branch
    MAIN_BRANCH=JIRA-14407-care2-merge python custolint mypy

    # code smell checking with pylint
    custolint pylint

    # code smell checking with flake8
    custolint flake8

    # 100% coverage checking for new commits implemented
    coverage run --branch -m pytest
    custolint coverage .coverage


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

How to contribute:
==================

For developers and contributors see the instruction here `<docs/for_developers.rst>`_.
