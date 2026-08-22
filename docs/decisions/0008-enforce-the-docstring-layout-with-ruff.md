---
date: 2026-08-17
---

(adr-0008)=
# ADR-0008 Enforce the docstring layout with ruff

## Context and Problem Statement

Docstrings here start their text on the line after the opening quotes,
and docformatter enforced that layout while also wrapping summaries and
descriptions at 79 columns. Its newest release refills prose that was
wrapped by hand and reads a raw string that is not a docstring as one.

ruff already runs over the same tree, and its `D213` checks the layout
with a fix available, while `W505` reports a doc line past a configured
length. Neither reflows prose, which is the behaviour that fights an
author.

## Considered Options

1. **Enforce the layout with ruff**, and drop docformatter.
2. **Keep docformatter on its previous release**, unbumped.
3. **Keep docformatter and configure around it**, excluding the file it
   mishandles and disabling description wrapping.

## Decision Outcome

Option 1. `D213` and `W505` join the pinned rule selection, and the
docformatter hook and its `[tool.docformatter]` table go. Wrapping
becomes the author's, which is how the prose in this repository was
written.

Option 2 holds a pin against a tool whose behaviour is the reason to
hold it. Option 3 keeps a second formatter for one rule ruff already
carries, and pays for it with a file-level exclusion.

## Consequences

An overlong doc line is reported rather than rewrapped, and no tool
refills a paragraph. The layout stays enforced, with a fix, and the hook
set is ruff alone.

The shared template and the Python guideline that named docformatter as
the enforcer followed this record rather than outliving it, so a
repository generated after it installs the same hook set as this one.
