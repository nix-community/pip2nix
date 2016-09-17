pip2nix
=======

Generate nix expressions for Python packages.

.. image:: https://travis-ci.org/johbo/pip2nix.svg?branch=master
   :target: https://travis-ci.org/johbo/pip2nix
   :alt: Build Status

.. image:: https://readthedocs.org/projects/pip2nix/badge/?version=latest
   :target: http://pip2nix.readthedocs.org/en/latest/
   :alt: Documentation Status

.. image:: https://img.shields.io/pypi/status/pip2nix.svg
   :target: https://pypi.python.org/pypi/pip2nix
   :alt: PyPI status

.. image:: https://img.shields.io/pypi/v/pip2nix.svg
   :target: https://pypi.python.org/pypi/pip2nix
   :alt: PyPI version

Why another .nix generator for Python?
======================================

I needed something that can work not only with pypi but also with local paths, VCS links, and dependency links.
I couldn't get any of the other generators to work, so I started my own :-)

Installation
============

::

    $ git clone https://github.com/johbo/pip2nix
    $ nix-env -f pip2nix/release.nix -iA pip2nix.python34  # Same Python as target packages

Usage
=====

To generate python-packages.nix for a set of requirements::

    $ pip2nix generate -r requirements.txt

``pip2nix generate`` takes the same set of package specifications ``pip install`` does.

Contact
=======

Problems and questions should go to GitHub `issues <https://github.com/johbo/pip2nix/issues>`_.


Credits
=======

Tomasz Kontusz started the project back in 2015 he's ktosiek on Freenode, and
`@tkontusz <https://twitter.com/tkontusz>`_ on Twitter.
