For developers
==============

1. Fetch code source

.. code-block:: bash

    git clone https://github.com/a-da/custolint.git


2. Install dev version

.. code-block:: bash

    $ make install_dev
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

4. Open Pull Request

.. code-block:: bash

    git commit ...
    git push ...

5. Push new package into PyPi

.. code-block:: bash

    $ make deploy_to_pypy
    rm -rvf build dist
    ...
    python -m build . --wheel
    ....
    Successfully built custolint-...-py3-none-any.whl
    twine upload dist/*
    Uploading distributions to https://upload.pypi.org/legacy/
    Enter your username: ...
    Enter your password: ...
    Uploading custolint-...-py3-none-any.whl
