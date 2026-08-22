======
Design
======

Problem
=======

A Nix build needs every Python package pinned: a version, a source, a
hash, and the packages it depends on. Python's own tooling resolves
requirements well, but expresses the result in formats a Nix build
cannot consume, and re-resolves from a moving index every time it runs.

pip2nix generates that pinned description as a file meant to be
committed: readable, diffable, and reviewable like the code depending
on it.

Approach
========

Two ideas carry the design.

**Get the user eighty percent of the way, and expect the rest by
hand.** Python metadata does not describe what Nix needs for the
difficult packages, so pip2nix does not attempt them. It generates the
routine majority and assumes a hand-maintained layer on top for
everything else. See :doc:`principles`.

**Let pip resolve, and translate what it resolved.** pip runs as a
subprocess and is asked for an installation report, the documented
JSON description of what it would install. pip2nix reads that report
and renders a Nix overlay from it. Resolution stays with the tool that
owns the problem; pip2nix owns the translation. See :ref:`ADR-0001 <adr-0001>`.

Known limits
============

Properties of the design rather than defects awaiting a fix:

- Resolution happens against the interpreter pip runs under. A
  requirement set that resolves differently per Python version or
  platform is resolved for the generator's environment, not the
  consumer's.
- Every package is emitted with ``doCheck = false``. Tests are not run.
- What a green build proves depends on the builder. A ``wheel`` or
  ``pyproject`` package is checked against its own metadata: the build
  fails unless every ``Requires-Dist`` is present and satisfies its
  version specifier. A ``setuptools`` package carries no such check, so
  a green build there says only that the source unpacked and installed.
  Neither says that the package works.
- Test dependencies are not generated. A consumer that wants the check
  phase adds a check hook and ``nativeCheckInputs`` in the overrides
  file; ``doCheck = true`` alone runs nothing. See
  :ref:`ADR-0011 <adr-0011>`.
- Native dependencies are not discovered. They belong in the overrides
  file.
- What a regeneration reuses is what the Nix store still holds. The
  recovered hashes let nix answer from it, but nothing roots those
  paths, so a garbage collection puts the downloads and the clones back.
- Build backends are named, not pinned. The installation report carries
  runtime dependencies only, so a name in ``nativeBuildInputs`` is a
  reference the generated file does not define, and nixpkgs decides
  which version satisfies it. Pinning them would take a resolution pass
  of its own.
- Following from that, a build requirement pinned to an exact version
  cannot be satisfied. A ``pyproject`` build checks
  ``build-system.requires`` against the environment before it starts,
  and a range is what nixpkgs can answer -- ``httptools`` asking for
  ``setuptools==80.9.0`` is not. Such a package needs
  ``pypaBuildFlags = [ "--skip-dependency-check" ]`` in the overrides
  file. A ``setuptools`` build never reads the field, so this surfaces
  only for projects declaring a build system -- the same split that
  decides which checks a build carries.
- Only git repositories are rendered. A requirement from another
  version control system fails rather than producing something
  plausible.
