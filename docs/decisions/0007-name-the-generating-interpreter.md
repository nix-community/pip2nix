---
date: 2026-08-16
---

(adr-0007)=
# ADR-0007 Name the generating interpreter in the installed command

## Context and Problem Statement

pip2nix resolves requirements against the interpreter pip runs under,
which `architecture/design.rst` records as a property of the design.
The flake targets `.#pip2nix_python311` to `.#pip2nix_python313` pick
that interpreter per build, but every build installs the same
unversioned command, so several of them cannot be told apart once
installed.

The versioned names that existed for this collided across all
supported interpreters, and a static `pyproject.toml` cannot compute
them at all.

## Considered Options

1. **Have Nix build the versioned name**, from the interpreter it
   already knows.
2. **Drop the versioned names**, leaving the flake targets as the only
   answer.
3. **Keep computing them in packaging metadata.**

## Decision Outcome

Option 1. `default.nix` symlinks `pip2nix${python.pythonVersion}` beside
`pip2nix`. Nix selects the interpreter, so Nix is where its name is
known.

Option 2 is cheaper and was close. It gives up installing more than one
build at a time, which is the case the versioned name exists for.
Option 3 is not expressible in static metadata, and is what produced
the collision.

The bare `pip2nix3` does not come back. It collides between the builds
by construction, which is the defect rather than a name worth keeping.

## Consequences

With more than one build installed, each is reachable under its own
name and resolves to its own store path. The unversioned `pip2nix`
still belongs to whichever build the profile gives priority, as it
would for any two versions of one package.

The entry point metadata stays static, so the packaging declares names
rather than computing them.
