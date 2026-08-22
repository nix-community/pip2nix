---
date: 2026-08-20
---

(adr-0015)=
# ADR-0015 Ask the invoking environment's nixpkgs about licenses

## Context and Problem Statement

`--licenses` maps a declared license name onto a `lib.licenses`
attribute by evaluating `<nixpkgs>` with `nix-instantiate`. That path
resolves from `NIX_PATH`, which the devShell and the Nix build set and
which the installed wrapper and a `pip install` do not, so which
nixpkgs answers depends on where pip2nix was invoked and the run says
nothing about it. Where `NIX_PATH` carries no `nixpkgs`, the flake
registry answers instead and fetches from channels.nixos.org without a
timeout.

The attribute that comes back is rendered into the generated file,
which the consumer evaluates against their own nixpkgs.

## Considered Options

1. **The invoking environment** — keep `<nixpkgs>`, report the store
   path it resolved to, and bound the resolution.
2. **The flake's pin** — set `NIX_PATH` in the installed wrapper, so a
   built pip2nix answers from the nixpkgs it was built with.
3. **A configuration option** — name the nixpkgs to query in
   `pip2nix.ini`.

## Decision Outcome

The invoking environment. A rendered attribute has to exist in the
consumer's nixpkgs rather than the generator's, and the environment the
command runs in is the only thing that knows which that is — pinning
the flake's nixpkgs would make a run reproducible while answering from
the wrong tree, and would leave an install outside Nix ambient anyway.
A configuration option asks every consumer to state what the invocation
already implies, on a surface {ref}`ADR-0006 <adr-0006>` narrowed.

What ambient resolution lacked was not a pin but a statement: the run
names the nixpkgs that answered, and one that does not resolve fails
within a bounded wait instead of blocking on a fetch.

## Consequences

Two machines can still generate different license attributes from the
same inputs. That is now visible in the run rather than silent, and
reproducing a generated file means reproducing the `NIX_PATH` it was
generated with.

## Related

- {ref}`ADR-0010 <adr-0010>` — the renderer is handed its
  collaborators, the license lookup among them.
- {ref}`ADR-0006 <adr-0006>` — per-package configuration dropped, the
  surface this decision declines to widen.
