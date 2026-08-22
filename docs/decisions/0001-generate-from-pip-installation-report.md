---
date: 2026-08-11
---

(adr-0001)=
# ADR-0001 Generate from pip's installation report

## Context and Problem Statement

pip2nix obtains the dependency graph it renders from `pip._internal`,
which pins it to pip 20.1.1 (2020) and blocks the move to current
nixpkgs and Python. The revision tagged `working-generator` still
generates; the modernization branch does not.

pip's legacy resolver and the private attribute pip2nix reads still
exist in pip 25.3 and 26.2.1, so a port is possible and touches roughly
200 of `generate.py`'s 401 lines. pip's own source records an intent to
remove them, and pip documents everything under `pip._internal` as
subject to change without notice. During the 20-to-25 window
`req.is_direct` kept its name and changed its meaning, so a port that
misses it emits a wrong package set without failing.

Separately, `pip install --report` produces JSON that is documented,
versioned and stable since pip 23.0, carrying per package the name,
version, source URL, hash, declared dependencies and a flag marking
whether the user requested it. A `uv.lock` parser was spiked at 149
lines with the existing renderer unchanged. uv2nix was used in one
consumer previously and required about 25 hand-written overlay entries.

## Considered Options

1. **Port to pip internals (B)** — update the existing resolver-driven
   code to current pip.
2. **Pip installation report (B')** — run pip as a subprocess and parse
   its `--report` JSON.
3. **uv.lock parser (C)** — delegate resolution to uv and parse its
   lock file.
4. **uv2nix** — replace pip2nix with eval-time derivation generation.

## Decision Outcome

Generate from pip's installation report.

It is the only interface examined that is documented, versioned and
supported, and it supplies everything the renderer needs, including a
direct/transitive flag matching what `only_direct` requires. pip remains
the resolver, so the `pip2nix.ini` and requirements-file workflow the
consumers already use is preserved and no consumer has to change.

The port was rejected despite being feasible and cheap, because it buys
back the exact liability this decision exists to remove. The `is_direct`
case is the argument: pip's own code was correct throughout, and pip2nix
would still have produced a wrong package set, silently. Reading
published data instead of private attributes trades a risk that no test
can catch for one that unit tests can.

C and uv2nix are rejected together, because both hand resolution to uv.
`uv.lock` is a vendor format with no published stability promise, and
uv2nix gives up the committed, diffable Nix file that is pip2nix's
reason to exist. PEP 751 `pylock.toml` does not rescue C: it carries no
direct/transitive marker, and no tool emits its optional dependency
table.

## Consequences

The report records each package's *declared* dependencies rather than
the resolver's chosen edges, so pip2nix has to attribute edges itself.
Parsing and marker evaluation are delegated to `packaging`, the same
library pip uses internally, and candidate edges are intersected with
the resolved package set. Marker evaluation cannot be skipped: on a
sample resolution, intersection alone produced 45 edges against 34
correct ones, and the spurious edges included a cycle.

Extras propagation is the one bespoke piece. The report marks requested
extras on top-level entries only, so extras reaching a transitive
package have to be carried through the graph by pip2nix. No current
Tryton consumer uses extras; lead-radar uses one.

The report requires pip 22.2 or newer, which ties this work to the
nixpkgs and Python modernization rather than allowing it to land first.

`models/package.py` imports pip as a library and extracts metadata from
built sdists. That coupling survives this decision and is the remaining
place where pip's internals still matter.

If the report proves inadequate, the fallback is the `working-generator`
revision, which keeps generating meanwhile. Reviving the port would then
be a fresh decision, recorded in a new ADR rather than promised here.

## Related

- pip installation report format:
  <https://pip.pypa.io/en/stable/reference/installation-report/>
- PEP 751, the standardised lock file format:
  <https://peps.python.org/pep-0751/>
