---
date: 2026-08-19
---

(adr-0012)=
# ADR-0012 Pin the pre-commit hooks by revision

## Context and Problem Statement

`.pre-commit-config.yaml` pins `ruff-pre-commit` at the tag `v0.16.3`. A
tag is a mutable ref, and pre-commit caches a hook repository per
revision, so the same configuration can resolve to different code on
different machines without anything in this repository changing.

The default repository template pins the same hook, which raises who
maintains the pin from here. This repository was not generated from that
template — it carries no copier answers file — so it inherits nothing
from it.

## Considered Options

1. **Pin by commit sha**, with the tag it came from in a comment, and
   maintain the pin in this repository.
2. **Keep the tag**, and take hook versions from the template.

## Decision Outcome

Option 1. A sha is content-addressed, so the configuration names the
revision that lints this tree rather than a ref whose meaning can change
under a checkout that has not. The exposure today is small — one hook,
one well-known publisher, and no CI job runs the hooks — so what decides
it is the inconsistency rather than the threat: everything else here is
locked.

The pin is this repository's because the hook version is what breaks
this tree, which is the reasoning {ref}`ADR-0008 <adr-0008>` already
applies to the rule selection. Option 2 describes a mechanism that does
not exist: copier propagates on update rather than on release, and this
repository is not generated from the template at all.

## Consequences

Bumping the hook is `pre-commit autoupdate --freeze`, which writes the
sha and refreshes the comment. It updates to the newest tag before
freezing, so a version move arrives with any pin change unless the pin
is already newest.

## Related

- {ref}`ADR-0008 <adr-0008>` — names the ruff rule selection in
  `pyproject.toml` rather than inheriting it from the hook.
