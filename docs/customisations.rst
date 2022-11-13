==============
Customisations
==============

Configuration through OS environments:

.. automodule:: custolint.env

Configuration through command line interface

Contributor
-----------

Exclude and/or include contributors with CLI ``--contributors`` argument.

.. versionadded:: 0.0.7

    .. code-block:: bash

        # TODO: not implemented yet
        custolint \
            --contributors=Josh,Andrei,Joanna \
            --skip-contributors=Ben \
                mypy


Halt on N messages
------------------

.. versionadded:: 0.0.7

    .. code-block::

        # TODO: not implemented yet
        custolint --halt-on-N-messages=5 mypy
