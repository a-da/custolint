=========================
custolint - custom linter
=========================

**custolint** is a small library that help you customize your existing validations in pipelines:

Link to sphinx documentation [to be placed here] also a icon.

Implements:

- `Pylint <src/custolint/pylint.py>`_
- `Flake8 <src/custolint/flake8.py>`_
- `MyPy <src/custolint/mypy.py>`_
- `Python Coverage <src/custolint/coverage.py>`_


Motivation
----------

When you have a big old code base with thousands of lines, you can not just include a linter and enable 100% checks.

.. image:: https://www.meme-arsenal.com/memes/fb7dcfc4064d5b75e281d354590b13a5.jpg
  :width: 400
  :alt: You cannot just take and (Boromir meme)
  
Instead, you just enable 1% of the checks, which is very sad for a decent developer.

*Could you just enable to only check your changes ?* **YES**, you can.

There is a better solution for this ! Welcome **custolint** - custom linter.

Idea
----

TODO: draw a diagram.
Given we have a project alike custolint, where we:

- changed a the function ``custolint/git.py:_blame``
- added a new function ``custolint/generics.py:filer_output``

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
    |   |   |-- generics.py
    |   |   |-- git.py
    |   |   |-- mypy.py
    |   |   |-- pylint.py
    |   |   `-- typing.py
    |-- tests
    |   `-- test_custolint.py

1. We have to detect affected files with ``git diff`` and ``git blame``

- ``custolint/git.py``
- ``custolint/generics.py``

2. Run the linter tool (pylint, flake8, mypy, coverage ...) with all available feature enables (the configuration have to be placed into  ``config.d/`` folder) only on changed affected files or parse log/result of the linter tool.

3. Match changed code with the linters output, and consider only the match lines as failed lint criteria.

   It have to detect that ``custolint/generics.py:filer_output`` need unitest for coverage
and ``custolint/git.py:_blame`` introduce a mypy typing issue.

4. Fail or Report the build.


