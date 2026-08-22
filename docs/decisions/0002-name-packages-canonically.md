---
date: 2026-08-12
---

(adr-0002)=
# ADR-0002 Name generated packages by their canonical name

## Context and Problem Statement

pip2nix names every generated attribute after the distribution it
renders. The resolver driven path took that name from the requirement
string that introduced the package, normalized by setuptools'
`pkg_resources.safe_name`, which preserves case. The report path of
ADR-0001 has only the name each package declares for itself. The two
disagree — `Werkzeug` declared against `werkzeug` requested — and one
package is already spelled two ways across generated files, which
consumer overlays bridge with hand-written aliases.

`pkg_resources` is deprecated. PEP 503 defines the only published
normalization and `packaging.utils.canonicalize_name` implements it; it
lowercases, and nothing case-preserving is published.

## Considered Options

1. **Canonical name** — normalize with `canonicalize_name`.
2. **Declared name** — reimplement setuptools' rule in pip2nix.
3. **Dependent's spelling** — reproduce the old output.

## Decision Outcome

PEP 503 canonical names.

It is the one naming rule the ecosystem publishes, so pip2nix need not
own it; the alternatives copy distribution naming knowledge into this
codebase, one of them from an API scheduled for deletion. It is also
the only stable option, since a name stops depending on which dependent
pulled the package in. The cost is a one-off rename of the capitalized
attributes at the next regeneration.

## Consequences

Consumers regenerate and can drop the aliases that existed only to reach
nixpkgs' lowercase names. Recorded as a breaking change in the
changelog.

## Related

- [ADR-0001](0001-generate-from-pip-installation-report.md) — the
  report path that raised the question.
- PEP 503 normalized names:
  <https://peps.python.org/pep-0503/#normalized-names>
