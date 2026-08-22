---
date: 2026-08-20
---

(adr-0016)=
# ADR-0016 Read configuration through properties

## Context and Problem Statement

The composition root read `config["pip2nix"]["output"]` and three more
keys as nested dictionary lookups, so it knew the section name, the key
spelling and the value type, while nothing stated that type anywhere.

`Config` already answered three questions by name, untyped, in a `get_`
style Python reserves for a lookup that can miss or a call that does
real work.

Sprint 9 has been turning values into types — the source kinds, a
frozen `PythonPackage` — which raises whether the configuration should
become one too.

## Considered Options

1. **Properties on `Config`**, named after the keys they read.
2. **A frozen `Options` dataclass**, built in `validate()` and exposed
   by `Config`.
3. **`get_` methods**, consistent with the three that existed.

## Decision Outcome

Option 1. Attribute access is what Python states as the read surface,
and a property is how an attribute grows computation without moving a
call site. Option 3 is a Java-ism the language argues against, and the
two existing `get_` accessors that were plain reads moved with this
rather than standing as a precedent.

Option 2 is the better end state and is rejected on cost rather than on
merit: it introduces a second model of the option surface that has to
be kept in step with `confspec.ini`, where a property reads the
validated section directly. Nine keys guarded by
`tests/unit/test_option_surface.py` do not need two declarations. It
becomes the right move when something needs the options apart from the
file they came from.

## Consequences

`__getitem__` stays, because `test_option_surface.py` probes by key the
four options whose reader is `indexes` or `get_requirements` rather
than a property of their own. A property for each would be a reader
with no caller, which is the defect that test exists to catch.

`get_requirements` stays a method. It parses each line and yields, and
a property is expected to be cheap and to answer the same twice.

## Related

- {ref}`ADR-0006 <adr-0006>` — what the option surface is allowed to
  contain.
