---
date: 2026-08-14
---

(adr-0006)=
# ADR-0006 Drop per-package configuration

## Context and Problem Statement

`confspec.ini` declared a `[[package]]` section with
`additional_requirements`, `excluded_requirements` and an `[[[args]]]`
subsection rendered into the generated package. Nothing read it:
`Config.get_package_config()` had no caller, and
`PythonPackage.override()` lost its own when `generate.py` was deleted
({ref}`adr-0001`). A configuration file could declare all of it and
pip2nix would report success having applied none of it.

## Considered Options

1. **Drop it, and refuse a declaration.**
2. **Wire it to the report path**, making the feature real.
3. **Drop it silently**, letting an existing declaration be ignored.

## Decision Outcome

Option 1. Wiring it would make `models/package.py` read configuration,
the move already rejected when the build-system decision went to
`report.py` rather than to the renderer. It would also turn a
`pip2nix.ini` into a way to put arbitrary Nix into a build, since
`[[[args]]]` is placed verbatim into the generated file.

Option 3 fails mechanically: ConfigObj ignores a section its configspec
does not declare, so removing the declaration alone leaves the silence
that let this survive. The refusal is an explicit check in
`Config.validate()`, as the `-e` refusal is.

## Consequences

A file declaring the section now fails validation, naming what it
found, rather than generating as though the section had been applied.
What `[[[args]]]` reached for belongs to the overrides layer, where a
generated package is customized under the reader's own eye.

## Related

- {ref}`adr-0004` — a package Nix cannot satisfy is the overrides
  layer's business.
