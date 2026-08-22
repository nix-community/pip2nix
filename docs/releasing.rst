=========
Releasing
=========

A release turns what has accumulated since the last one into a version
a consumer can pin.


The release shell
=================

The tools come from a shell of their own::

    nix develop .#release

It carries ``cocogitto``, ``just``, ``towncrier``, ``twine`` and the
``pyproject-build`` frontend, pinned through ``flake.lock`` rather than
resolved on the day of the release.

Run everything below from that shell.


Recording a change
==================

Every change a consumer would notice adds a file under ``changelog.d/``;
the README there says how to name it and what to write. A release
collects the files into a version section in ``CHANGELOG.rst`` and
removes them, so two branches never edit the same lines and a merge
cannot conflict over the changelog.


Making the release
==================

Cocogitto works out the version, writes it into the files that record
it, assembles the changelog, commits the result and tags it::

    cog bump --auto

pip2nix is in ``0.y.z``, where a fix bumps the patch and a feature or a
breaking change bumps the minor -- which is what ``--auto`` derives.
Pass the increment for the one case it gets wrong: a breaking change
written as something other than a feature, which derivation bumps as a
patch.

Push the commit, see that it landed, and push the tag after::

    git push
    git push --tags

Both in one command publishes the tag even when the branch is rejected,
which leaves a release tag on a commit that is on no branch.


Where the version is written
============================

``just set-version`` writes it into ``pyproject.toml``,
``pip2nix/__init__.py``, ``docs/conf.py`` and the two generated lines in
``python-packages.nix``.

It is written into each rather than derived from one. The development
shell cannot contain pip2nix -- its package set is the one pip2nix
generates -- so there is no installed metadata to read a version from.
Every substitution is guarded, because ``sed`` reports a pattern that
matches nothing as success, which would release a version half the files
never received.

Where the release also changes what pip2nix generates, run ``just
regenerate`` after the bump and before pushing, so that
``python-packages.nix`` is what the released version produces rather
than the previous one with its header rewritten.


Two kinds of tag
================

``vX.Y.Z`` is a release, made by the procedure above.

``working-generator`` and ``working-generator-2`` are not releases. They
are pinned states a consumer resolves as a flake input, tagged so a
known-good generator stays reachable, and they carry no version series.
``working-generator-2`` is not an ancestor of master: the four fixes on
it were re-achieved on master by rewriting rather than merged forward,
because master had replaced the code they touch.

Keep the two namespaces apart, and never name a pinned state so that it
could be read as a version.


Publishing
==========

This fork publishes nothing -- uploading to PyPI stays upstream's, for
whenever the work lands there. The steps are here so that whoever makes
that release has an environment for it::

    just clean
    just dist
    just dist-check
    twine check dist/*
    twine upload dist/*

``just dist`` builds the source distribution and the wheel without build
isolation, so the backend is the ``setuptools`` the release shell
carries rather than one fetched from PyPI mid-build. ``just clean``
comes first because ``pyproject-build`` writes into ``dist/`` without
emptying it, so an earlier version would stay there and
``twine upload dist/*`` would offer it again.

``just dist-check`` installs each artifact into a virtualenv of its own
and generates with it, which is what catches one that installs but
cannot run -- package data that never made it in, or a dependency the
metadata does not declare. Its last pass installs into a virtualenv
carrying no pip, the kind ``uv`` and ``pipx`` create. ``twine check``
does not reach any of that: it reads the metadata and stops there.

The same two recipes run in CI, so an artifact is checked per commit
rather than only on the day of a release.
