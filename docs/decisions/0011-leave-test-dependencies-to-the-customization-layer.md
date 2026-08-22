---
date: 2026-08-17
---

(adr-0011)=
# ADR-0011 Leave test dependencies to the customization layer

## Context and Problem Statement

Every generated package carries `checkInputs = [];`. It was filled until
{ref}`adr-0001` deleted `generate.py`, and is now a literal in the
renderer that nothing assigns. Rebuilding it is possible: pip's report
carries `provides_extra` and the extra-gated `requires_dist` entries
beside it, and `dependencies.py` already traverses extras.

## Considered Options

1. **Leave them to the customization layer** — stop emitting the
   attribute.
2. **Build them from a declared extra** — an option in `confspec.ini`
   naming which extra is the test one.
3. **Keep emitting the empty attribute.**

## Decision Outcome

Option 1, for the same reason native dependencies are already the
customization layer's. Every package is generated with `doCheck =
false` and no consumer overrides it, so a filled attribute would do
nothing; and `checkInputs` is not the attribute for it in current
nixpkgs, where test tools needed on `$PATH` belong in
`nativeCheckInputs`. Option 2 would additionally put configuration in
front of a renderer {ref}`adr-0006` keeps out of it.

## Consequences

`buildInputs` stays, though it is equally unfilled: overrides append to
it, which nothing does for `checkInputs`. An attribute nothing reads and
an attribute an override extends look alike in the generated file.

## Related

- {ref}`adr-0006` — configuration the renderer would have had to read.
