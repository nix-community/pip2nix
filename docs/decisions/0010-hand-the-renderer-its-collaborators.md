---
date: 2026-08-17
---

(adr-0010)=
# ADR-0010 Hand the renderer its collaborators

## Context and Problem Statement

{ref}`ADR-0009 <adr-0009>` decided that the renderer resolves a source
hash and a license attribute while it renders, and deferred how it is
given what resolves them. It imported them: `models/package.py` reached
for `prefetch.py` and `models/license.py` for `licenses.py`, while the
licenses flag and the hash cache travelled through three parameter
lists.

## Decision Outcome

`cli.py` constructs a `Rendering` and passes it in. It carries the two
prefetch functions, the `nixpkgs.lib.licenses` lookup, whether licenses
are rendered, and the hashes recovered from the previously generated
file.

Rendering imports no infrastructure as a result. *When* resolution
happens is unchanged, so this refines ADR-0009 rather than superseding
it: the renderer still resolves while it renders, and still resolves
only what a run actually asks for.

## Consequences

A unit test of the renderer constructs its stand-ins rather than
patching a name in another module, and
`tests/unit/test_renderer_independence.py` fails if an import creeps
back.
