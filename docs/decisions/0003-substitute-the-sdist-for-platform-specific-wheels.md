---
date: 2026-08-12
---

(adr-0003)=
# ADR-0003 Substitute the sdist for platform-specific wheels

## Context and Problem Statement

pip resolves to wheels, and pip2nix renders what it resolved. A wheel
built for a platform links against libraries at paths that do not exist
in the Nix store, so `buildPythonPackage` installs it and the import
fails at runtime. The resolver driven path replaces any wheel that is
not `-any` with the project's sdist; the report path of ADR-0001 does
not, and emits the binary wheel.

Which artifact a package is built from is therefore a rule pip2nix owns,
and the report carries no build-system information at any level — not
the requires, not the backend — because core metadata has none. Wheels
need none of it; sources do.

## Considered Options

1. **Non-`-any` wheels only** — substitute where the wheel cannot be
   used, leave pure-Python wheels alone.
2. **Prefer sources everywhere** — resolve every package from its sdist.
3. **Render what pip resolved** — emit the wheel pip chose.

## Decision Outcome

Substitute for non-`-any` wheels only.

Preferring sources everywhere was measured against the real consumers
rather than argued: `--no-binary :all:` applies to build dependencies
too, so `nix-tryton` fails after 356 seconds trying to compile CMake, to
build ninja, to build pybind11, to build a package that is transitive
and never emitted. Restricted to the emitted names it resolves, but the
output is not renderable — `relatorio` ships no `setup.py` and builds
with a Tryton-specific hatchling plugin that appears in no resolution
pip gives us and in no nixpkgs attribute. Rendering the wheel pip chose
was rejected because it silently drops the guarantee that the generated
file builds.

The narrow rule is the one that holds: a pure-Python wheel and its sdist
carry the same modules, so substituting there buys nothing, while a
platform-specific wheel is the case Nix genuinely cannot consume.

## Consequences

Sources need their build backends, so `build-system.requires` is read
from the source itself — the report cannot supply it. Substituting
requires a second resolution restricted to the affected packages, which
costs nothing for consumers that have none.

Preferring sources everywhere stays possible, but it needs three things
first: detecting the build format instead of assuming setuptools,
extracting the build requires, and resolving the build dependencies
themselves so the emitted references exist.

## Related

- [ADR-0001](0001-generate-from-pip-installation-report.md) — the
  report path that dropped the substitution.
