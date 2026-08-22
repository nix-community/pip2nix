============
Architecture
============

pip2nix turns a set of Python requirements into a Nix expression
pinning every package that was resolved. This chapter says how the
generator is built and what shaped it.

Context and scope
=================

Whoever maintains a Nix package set for a Python project runs pip2nix.
They state the requirements, run ``pip2nix generate``, and commit what
it wrote. A Nix build reads it afterwards; they do not.

The generator reads its configuration, runs pip, translates the report
pip wrote, resolves every source into something Nix can fetch, and
renders the file. The rest belongs elsewhere: pip resolves, a later
Nix run builds, and whatever Python metadata cannot express is the
customization layer's -- hand-maintained, written once by ``pip2nix
scaffold``, and never written by pip2nix again. See
:doc:`architecture/principles`.

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Talks to
     - For
   * - pip, as a subprocess
     - Resolving the requirements into an installation report.
   * - The package index
     - Reached only through pip.
   * - ``nix-prefetch-url`` and ``nix-prefetch-git``
     - A source's hash, and the copy in the store its metadata is read
       from. A repository is fetched at the :term:`commit ID` pip
       resolved it to.
   * - ``nix-instantiate`` and a ``<nixpkgs>``
     - A ``lib.licenses`` attribute, under ``--licenses`` only.
   * - The previously generated file
     - A hash it already answered, so that a regeneration fetches
       nothing it need not.

A generation run writes one file and overwrites it whole, so nothing
put into it by hand survives. That is what the layer above it is for.

Quality goals
=============

These four properties are what the architecture is optimised for, and
what a change to it is weighed against.

- **The generated file survives review.** Someone reads the diff of a
  regeneration and has to be able to say what moved. Canonical names
  and a single hash alphabet are there for that, and they are why a
  change of encoding is not a change. See
  :doc:`architecture/principles`.
- **A run states what it depended on.** Every source is pinned by the
  hash it was fetched with, and the one input that resolves from the
  environment instead is named by the run rather than left silent. See
  :ref:`ADR-0015 <adr-0015>`.
- **A run that cannot be correct stops.** The cost of a wrong
  generated file falls at build time or later, on someone who did not
  run the generator. See :doc:`architecture/principles`.
- **The generator stays small.** A package it cannot describe from
  metadata is one it does not attempt, which is what keeps the code
  small enough to keep working on. See :doc:`architecture/design`.

Constraints
===========

Given rather than chosen. The architecture works within them.

- **The installation report is pip's format.** pip2nix reads what pip
  publishes and validates the version the report declares; writing one
  at all takes pip 22.2 or newer. See :ref:`ADR-0001 <adr-0001>`.
- **The output has to be what ``buildPythonPackage`` accepts.** Nix
  evaluates it long after the run that wrote it, so the generator gets
  no feedback from the build it is writing for.
- **Python packaging metadata is the only description of a package
  there is.** Nix needs facts about a build that Python never asks a
  project to state, and no amount of work on the generator conjures
  them.
- **Every source is fetched by a Nix fetcher.** Its hash therefore has
  to be known by the time the file is written, not at the time it is
  built.

.. toctree::
   :maxdepth: 2

   architecture/design
   architecture/building-blocks
   architecture/runtime
   architecture/principles
