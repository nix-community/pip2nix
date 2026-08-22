---
date: 2026-08-21
---

(adr-0017)=
# ADR-0017 Keep the base32 encoder in Python

## Context and Problem Statement

`nix_base32.from_hex` re-encodes the hex sha256 an index publishes into
the alphabet a `fetchurl` `sha256` attribute expects. It has one caller,
`Sources.resolved`, and thirty lines of pure Python behind it.

Sprint 7 measured that `nix` can do the same: `nix hash convert` is
documented as `[option...] hashes...`, and two digests in one call
returned byte for byte what `from_hex` returns. It deferred on placement
alone -- converting during rendering would have meant a second
subprocess inside `Rendering`, or pulling the {ref}`adr-0009` revisit
forward into that sprint.

{ref}`adr-0014` landed that revisit, so placement is no longer an
objection: hex digests are converted in the adapter, where one call for
all of them is the natural shape. The question is now only whether the
module earns its thirty lines, and it has been asked three times without
being written down.

## Considered Options

1. **Keep `nix_base32.py`.**
2. **One batched `nix hash convert`** over every archive digest, in the
   adapter.
3. **One `nix hash convert` per digest.**

## Decision Outcome

Option 1. `nix hash convert` belongs to the `nix` command, which prints
"This program is experimental and its interface is subject to change" on
every invocation without the feature flag. Options 2 and 3 put that
interface on the critical path of every generation run, and buy the
removal of thirty lines that have not changed since they were written.

The module's four tests hold it to reference values produced by `nix
hash convert` itself and need no doubles. A subprocess would need a
stand-in in every test that renders an archive source, which is most of
them.

Option 3 is worse than option 2 on top of that: a real consumer's report
names hundreds of archives, and each would cost a process.

## Consequences

The question stays answered only as long as the reason is visible, so
the module's docstring carries it and points here.

`tests/unit/test_nix_base32.py` is what keeps the encoder honest. Its
reference digests came from `nix hash convert`, so a divergence between
the two implementations fails there rather than in a generated file.

This is a decision about a helper, not about shelling out in general.
Nothing here argues against the `nix-prefetch-*` calls in `prefetch.py`,
which do work no Python can do locally.

## Related

- {ref}`adr-0014` -- moved the conversion into the adapter, which is what
  made the placement objection moot.
