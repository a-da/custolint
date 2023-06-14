For developers
==============

1. Fetch code source

.. code-block:: bash

    git clone https://github.com/a-da/custolint.git


2. Install dev version

... the same copy of snippet is available in readme, TODO: unify

.. code-block:: bash

    $ make update_pip_and_wheel install_dev
    pip install -e .[dev]
    Obtaining file:///Users/.../github.com/custolint
    Installing build dependencies ... done
    ...
    Successfully installed custolint-....

3. Validate your changes

.. code-block:: bash

    $ make validate
    coverage run --branch -m pytest
    ...
    tests/test_custolint.py .... [100%]

    MAIN_BRANCH='master' custolint coverage .coverage
    ...
    MAIN_BRANCH='master' custolint pylint
    ...
    MAIN_BRANCH='master' custolint flake8
    ...
    MAIN_BRANCH='master' custolint mypy

5. Increase version (manually) of the package to be release ``setup.cfg:version``

4. Open Pull Request

.. code-block:: bash

    git commit ...
    git push ...

5. Github Action will be triggered see https://github.com/a-da/custolint/actions
