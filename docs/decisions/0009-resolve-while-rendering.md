---
date: 2026-08-17
---

(adr-0009)=
# ADR-0009 Resolve while rendering

**Status: Superseded by {ref}`ADR-0014 <adr-0014>`**

## Context and Problem Statement

The design chapter places `prefetch.py` and `licenses.py` under
Infrastructure and `models/package.py` under Rendering, and states that
dependencies point inward. The renderer imports from both: a source hash
comes from `nix-prefetch-url`, a `lib.licenses` attribute from
`nix-instantiate`.

Neither value is in pip's report. A hash is known once the archive is
fetched, an attribute only by asking the nixpkgs the generated file will
be evaluated against.

## Considered Options

1. **Resolve while rendering** -- the renderer calls infrastructure for a
   value it cannot render without.
2. **Resolve in the adapter** -- `report.py` obtains both and hands the
   renderer resolved values.
3. **Invert the dependency** -- the renderer declares what it needs and
   the composition root passes an implementation in.

## Decision Outcome

Option 1, as the design rather than an accident. Rendering is where it is
known which values are still missing: a hash already in the previously
generated file is never fetched, and no license is looked up when
`--licenses` is off.

Option 2 gives the pip adapter a dependency on nixpkgs and on the
network, and resolves for runs that never ask. Option 3 is the correct
inversion, deferred rather than rejected: the render flags and the
collaborators travel together through three functions, so it is a value
object rather than a parameter.

## Consequences

A unit test of the renderer stands in for the lookup rather than reaching
nixpkgs.

Rendering reaches the network and the Nix store, so it can fail. The
output file is therefore opened only once every package has rendered,
which is what keeps a failed run from truncating the previous one.

The import guards cannot see this. A collaborator called while rendering
crosses no import, so `test_renderer_independence.py` passes whether the
call is there or not.
