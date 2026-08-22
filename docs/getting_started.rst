===============
Getting started
===============

Installation
============

`pip2nix` is a flake, so it can be run without installing anything::

  $ nix run github:johbo/pip2nix -- generate -r requirements.txt

To keep a build around, clone the repository and build it::

  $ git clone https://github.com/johbo/pip2nix
  $ cd pip2nix
  $ nix build

The generator is then ``./result/bin/pip2nix``, with
``./result/bin/pip2nix3.13`` beside it naming the interpreter this
build resolves against -- which is what tells two builds apart on one
``PATH``. ``nix build`` builds the default target, which is Python
3.13. The targets ``.#pip2nix_python311`` up to
``.#pip2nix_python314`` build against a specific interpreter.

That choice is not cosmetic: pip2nix resolves requirements against the
interpreter it runs under, not against the one the generated packages
are built with. See :doc:`architecture/design`.


Installing without Nix
======================

pip2nix is a Python package as well, so it installs the way any other
does::

  $ pip install pip2nix
  $ uv tool install pip2nix
  $ pipx install pip2nix

Such an install carries the single command ``pip2nix``. The versioned
names beside it belong to the Nix build, which is the only installer
that knows the interpreter a build resolves against -- see
:ref:`ADR-0007 <adr-0007>`. Install pip2nix into the interpreter you
generate for, for the same reason the flake has a target per version.

What it generates goes into the Nix store either way, so the tools that
put it there have to be on ``PATH``:

``nix-prefetch-url``
    Every source that is a file.

``nix-prefetch-git``
    Sources given as a git repository.

``nix-instantiate``
    Only ``--licenses``, which asks nixpkgs which licenses it knows,
    and needs a ``<nixpkgs>`` that resolves as well.

A tool that is missing is named in the error, so a run fails on the
first thing it cannot do rather than part way through the file.

Which nixpkgs answers is the one ``NIX_PATH`` supplies, and the run
names its store path before it asks. Where ``NIX_PATH`` carries no
``nixpkgs`` entry, the flake registry is fetched from instead, and the
run gives that up after 30 seconds rather than waiting on it. See
:ref:`ADR-0015 <adr-0015>` for why the environment decides this rather
than pip2nix.


Basic usage
===========


Ad-hoc python-packages.nix generation
-------------------------------------

To generate python-packages.nix for a set of requirements::

    $ pip2nix generate -r requirements.txt

``pip2nix generate`` understands requirement files (``-r``), package
specifications and git links, spelled the way ``pip install`` spells
them. Two kinds of requirement are rejected rather than resolved:

Editable requirements (``-e``)
    The installation report describes them as the local directory they
    would be checked out into, which loses the url and the revision
    they come from.

Mercurial repositories (``hg+``)
    Only git repositories are rendered.

Both abort the run and name the requirement, rather than generating
something plausible.


Using pip2nix in a project
--------------------------

When packaging a project with pip2nix you'll want to make sure it's called the
same way every time you bump dependencies. To do that, you can create a
``pip2nix.ini`` file::

    [pip2nix]
    requirements = -r ./requirements.txt

This way you can just run ``pip2nix generate`` in the project's root.
More about the configuration file in :doc:`configuration`.

To actually use the generated packages file, you can create a default.nix with
``pip2nix scaffold``. To work on a project `my-project` you'd use::

    $ pip2nix scaffold --package my-project
    $ cat > pip2nix.ini <<EOF
    [pip2nix]
    requirements = .
    EOF
    $ pip2nix generate
    $ nix-shell  # all the deps should be available

The name is canonicalized before it is written -- lowercased, with
underscores and dots turned into hyphens -- so the scaffold refers to
the package under the same name the generated file defines it under.
``--package My_Project`` and ``--package my-project`` produce the same
file. See :doc:`architecture/principles`.
