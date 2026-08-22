# Configuration file for the Sphinx documentation builder.

# -- Project information -----------------------------------------------------

project = "pip2nix"
copyright = "2015-%Y, the pip2nix authors"
author = "the pip2nix authors"

release = "0.13.1"
version = ".".join(release.split(".")[:2])


# -- General configuration ---------------------------------------------------

extensions = [
    "myst_parser",
    "sphinx.ext.extlinks",
    "sphinx.ext.ifconfig",
    "sphinx.ext.intersphinx",
    "sphinx.ext.todo",
]

exclude_patterns = [
    "_build",
    "decisions/README.md",
]


# -- Options for HTML output -------------------------------------------------

html_theme = "sphinx_book_theme"

html_static_path = []


# -- Options for PDF output --------------------------------------------------

latex_documents = [
    ("index", "pip2nix.tex", "pip2nix Documentation", author, "manual"),
]


intersphinx_mapping = {}
