---
date: 2026-08-14
---

(adr-0004)=
# ADR-0004 Leave a pinned build requirement to the overrides layer

## Context and Problem Statement

Rendering `format` from the declared build backend moves a package that
declares a `[build-system]` table from the `setuptools` builder to the
`pyproject` one. The two treat `build-system.requires` differently: the
setuptools builder never reads the field, the pyproject builder checks
it against the environment before the build starts.

The generated file names build backends without pinning them, so nixpkgs
decides which version satisfies a name ({ref}`adr-0003`). A range is
therefore satisfiable and an exact pin is not. Measured across all four
consumers, one of the eight affected packages pins exactly: `httptools`
requires `setuptools==80.9.0` and fails to build. The other seven
declare ranges and build.

## Considered Options

1. **Leave it to the overrides layer** — document the limit and let a
   consumer add `pypaBuildFlags = [ "--skip-dependency-check" ]`.
2. **Emit the flag for every pyproject package** — so no consumer has
   to add it.
3. **Emit the flag only where a requirement is pinned** — read the
   specifier operators and generate the flag for those packages.

## Decision Outcome

Option 1. The check passes for seven of the eight affected packages, so
disabling it everywhere would remove a working safeguard to accommodate
one — and would take with it the range mismatches it does catch, which
are the cases nixpkgs can be made to satisfy. Option 3 keeps the
safeguard but renders two otherwise identical packages differently, and
adds specifier parsing for a case that occurred once.

A package whose own metadata cannot be satisfied in Nix is what the
hand-maintained overrides layer exists for.

## Consequences

Generation is unaffected; only the build of such a package fails, and it
names the requirement it is missing.

## Related

- {ref}`adr-0003` — build backends are named, not pinned.
