pip2nix
=======

Generate nix expressions for Python packages.

.. image:: https://travis-ci.com/nix-community/pip2nix.svg?branch=master
   :target: https://travis-ci.com/nix-community/pip2nix
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


About this fork
===============

This is a fork of `nix-community/pip2nix
<https://github.com/nix-community/pip2nix>`_, maintained by Johannes
Bornhold. The generator was rebuilt here in 2026 on pip's installation
report, and the work is meant to go back to nix-community rather than
to continue as a project of its own.

Releases are not published from this fork; publishing stays upstream's,
for whenever the work lands there. The links and badges above name
upstream for the same reason.


Why another .nix generator for Python?
======================================

The original author of `pip2nix` started the project with the following motivation:

  I needed something that can work not only with pypi but also with local paths,
  VCS links, and dependency links. I couldn't get any of the other generators to
  work, so I started my own :-)

Major difference between `pip2nix` and `pypi2nix` is that `pip2nix` can be used to extend `nixpkgs` Python package set and reuse its package functions where `pypi2nix` maintains separate package tree from `nixpkgs`. Both approaches have their own pros and cons.


Installation
============

Be aware that `pip2nix` is not yet mature software. It is a tool to aid Python
developers who use Nix to automate a good chunk of the work to maintain a Nix
based development environments.

The recommended usage at the moment is to build it and use the result,
since this avoids putting a specific version into the user's
environment::

  $ git clone https://github.com/nix-community/pip2nix
  $ cd pip2nix
  $ nix build
  $ ./result/bin/pip2nix generate -r requirements.txt

``nix build`` builds against Python 3.13, installing
``pip2nix3.13`` beside ``pip2nix`` to name the interpreter it resolves
against. The targets ``.#pip2nix_python311`` up to
``.#pip2nix_python314`` build against a specific interpreter, and
``nix develop`` gives a shell to work on pip2nix itself.



Usage
=====

To generate python-packages.nix for a set of requirements::

    $ pip2nix generate -r requirements.txt

Alternatively if having flakes enabled you can run `pip2nix` without the need to install it::

    $ nix run github:nix-community/pip2nix -- generate -r requirements.txt


``pip2nix generate`` understands requirement files (``-r``), package
specifications and git links, spelled the way ``pip install`` spells
them. Editable requirements (``-e``) and mercurial repositories are
rejected rather than resolved.


Contact
=======

Problems and questions should go to GitHub `issues
<https://github.com/nix-community/pip2nix/issues>`_.


Credits and History
===================

Tomasz Kontusz started the project back in 2015, he's `ktosiek` on Freenode, and
`@tkontusz <https://twitter.com/tkontusz>`_ on Twitter.

In 2016 Johannes Bornhold took over as maintainer, since he was actively using
`pip2nix` and Tomas was not actively using it himself anymore. Find him via
https://www.johbo.com.

In 2019 Asko Soukka forked the project below https://github.com/nix-community/
and took over as maintainer.

It fell into bad shape for a long stretch after that. The generator drove
pip's internal resolver API, which held it at pip 20.1.1 from 2020 and kept
it from following recent Python and nixpkgs releases.

In 2026 Johannes Bornhold picked maintenance up again, for his own needs.
The generator was rebuilt on pip's installation report, which is documented
and stable, so pip runs as a subprocess and any recent version will do.
Features that had stopped working along the way were removed rather than
carried along.


License
=======

GPL-3.0-or-later. The full text is in `LICENSE <LICENSE>`_, and each
contributor holds the copyright in their own work.
