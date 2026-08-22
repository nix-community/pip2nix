---
date: 2026-08-14
---

(adr-0005)=
# ADR-0005 Resolve one source distribution per pass

## Context and Problem Statement

{ref}`ADR-0003 <adr-0003>` replaces a wheel Nix cannot build from with
the project's source distribution, and pip2nix asked for all of them at
once: a single second resolution naming every affected package in one
`--no-binary`.

pip hands its format control on to the isolated build environments it
creates. `build_env.py` passes both `no_binary` and `only_binary`
verbatim to the build environment's own `pip install`, and
`format_control.py` gives a per-name `--only-binary` precedence over a
per-name `--no-binary`.

A package can therefore hold two roles in one run. lead-radar requests
`maturin` directly, and `maturin` is also the build backend of
`pydantic-core` and `watchfiles`, which are resolved from source beside
it. Refusing maturin a wheel for its own sake also refuses it to the
build environments that need it, so pip compiles it with cargo to read
another package's metadata: 6m44s where there is a toolchain, and a
hard failure where there is none. Nothing in the generated output
depends on that build.

The cost is easy to miss, because pip caches the wheel it built. The
second run on the same machine is fast, and the defect is visible only
against a cache that has not paid for it yet.

## Considered Options

1. **One pass naming every affected package** — what ADR-0003
   implemented.
2. **One pass, with `--only-binary` naming the known build backends** —
   sources for what is rendered, wheels for what merely builds it.
3. **One pass per package, naming only that package.**

## Decision Outcome

One pass per package.

Option 2 cannot express the two roles: naming maturin in
`--only-binary` wins over `--no-binary` for the rendered package too,
which is the platform-specific wheel ADR-0003 exists to keep out. It
also needs a list of backend names to be maintained, and the report
carries no build-system field to derive one from.

Option 3 needs no such list. A pass names one package, so every other
name is free to arrive as a wheel wherever pip needs it. The pass
carries `--no-deps` and pins the version the requirements resolution
already produced, which is what leaves nothing else to resolve.

This refines how ADR-0003 is carried out. Which packages take their
source is unchanged, and that record stands as written.

## Consequences

A generation runs one subprocess per package that needs its source
where it ran one in total. Each is a single pinned package with no
dependencies to resolve. Consumers whose wheels are all `-any` — the
Tryton set among them — still start no pass at all.

A build backend that builds itself, such as `setuptools`, `flit-core`
or `hatchling`, is still taken from source in its own pass. All of them
are pure Python, so the pass stays cheap; the case that costs is a
compiled backend, and no compiled backend builds itself.

The constraints from the configuration are not passed to a pass. The
pinned version came out of the resolution that honoured them, and
`--no-deps` leaves nothing for a constraint to bind.

`tests/integration/test_cold_cache.py` guards the decision, against a
pip cache created for the run, because a warm cache hides exactly what
it checks for.

## Related

- {ref}`ADR-0003 <adr-0003>` — which packages are taken from source,
  refined here in how they are asked for.
