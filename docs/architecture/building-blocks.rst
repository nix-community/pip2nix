===============
Building blocks
===============

The blocks below are listed the way a generation run moves through
them, and the dependencies point the same way: pip is a subprocess
nothing imports, and rendering imports nothing from infrastructure.
What each block does in sequence is
:doc:`a generation run <runtime>`.

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Block
     - Modules
   * - Composition root
     - ``cli.py``
   * - Adapter
     - ``config.py``, ``report.py``, ``dependencies.py``,
       ``build_system.py``
   * - Rendering
     - ``models/package.py``, ``models/source.py``,
       ``models/license.py``, ``nix_base32.py``, ``output.py``
   * - Infrastructure
     - ``resolver.py``, ``prefetch.py``, ``license_lookup.py``,
       ``resources.py``
   * - Below every block
     - ``errors.py``

Composition root
================

Resolves everything external to one run -- the configuration, the
interpreter that runs pip, the collaborators, the output path -- and
hands it inward. Nothing below it constructs a collaborator of its own.
It is the only block that reads an environment variable, and the only
place a failed run becomes a message rather than a traceback.

Adapter
=======

Turns the two external formats into the values the run consumes:
``pip2nix.ini`` and pip's installation report. ``config.py`` belongs
here rather than with the composition root because it is a parser and a
data type holding no wiring.

The block is handed what runs pip and what fetches a source, so the
report stops here: what it passes on carries no trace of pip. It also
answers the two questions the report cannot. Which build backend a
package declares means reading the source itself; and what a source is
fetched with -- a repository's hash, an archive's digest in the
alphabet Nix reads -- means resolving it, which the block does before
anything is rendered. See :ref:`ADR-0014 <adr-0014>`.

Rendering
=========

Turns those values into the Nix expression and writes the file.
``PythonPackage`` carries ``buildPythonPackage`` arguments rather than
facts about a Python package, so it renders itself instead of being
rendered by something else.

A package arrives with its source already resolved, so rendering one is
a function from a package to a string. The single thing this block
still cannot know is a license attribute, which arrives as
``NixLicenses`` from the composition root; see :ref:`ADR-0010
<adr-0010>` for why it is handed in rather than reached for.

``--licenses`` off arrives as ``NoLicenses``, which renders none. The
flag stops at the composition root rather than travelling to the one
site that reads it, so the block decides nothing about what a run was
asked for.

Infrastructure
==============

Everything that reaches outside the program: pip, the
``nix-prefetch-*`` tools, ``nix-instantiate``, and the packaged files a
scaffold is written from.
Every subprocess a generation run starts belongs here, and each is
constructed in the composition root, which is why neither the adapter
nor the renderer carries one of its own.

Below every block
=================

``errors.py`` holds the failures a run reports to its user, and nothing
else. The blocks above it raise from it and the composition root
catches, which is what keeps none of them importing another.

The seam the guards cannot see
==============================

Three tests enforce the boundaries above rather than describing them,
and all three check imports. One collaborator is used at runtime
instead: rendering ``meta.license`` asks ``NixLicenses``, which reaches
``nix-instantiate``. The direction is intact -- the call arrives
through a collaborator that was passed in -- but no guard sees it, and
it is why ``output.py`` finishes rendering before it opens the output
file. A source hash reached outside the same way until :ref:`ADR-0014
<adr-0014>` moved that resolution into the adapter.
