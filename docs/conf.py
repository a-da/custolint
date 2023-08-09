"""Configuration file for the Sphinx documentation builder."""
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html
from pathlib import Path

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'custolint'
copyright = '2022, Andrei Danciuc'  # pylint: disable=redefined-builtin,invalid-name # noqa: shadow
author = 'Andrei Danciuc'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration
master_doc = "index"
extensions = [
    "sphinx.ext.autodoc",
    "sphinx_click",
    "sphinxcontrib.programoutput",
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'pyramid'
html_static_path = ['_static']


def update_readme() -> None:
    """
    Adjust root readme for documentation.
    """
    _root_readme_rst = Path(__file__).parent.joinpath('..', 'README.rst')
    _content = _root_readme_rst.read_bytes()
    _content = _content.replace(b' image:: ./docs/', b' image:: ./')
    _content = _content.replace(b':name: given example', b':emphasize-lines: 6,7')
    _content = _content.replace(b'<./docs/', b'<./')
    _readme_rst = Path(__file__).parent.joinpath('.', 'readme.rst')

    _readme_rst.write_bytes(_content)


update_readme()
