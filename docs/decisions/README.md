# Decisions

Decision records for pip2nix, in the [MADR](https://adr.github.io/madr/)
style.

Files are named `NNNN-short-slug.md` with a sequential 4-digit prefix.
Gaps in the numbering are acceptable; do not renumber.

## Cross-referencing

Each record carries a MyST label, placed after the frontmatter and
before the heading:

```markdown
---
date: 2026-08-11
---

(adr-0001)=
# ADR-0001 Decision title
```

Reference one with the `{ref}` role — `` {ref}`adr-0001` `` — which
renders as a link carrying the record's title.

## Immutability

Records are immutable once accepted. When a decision changes, write a
new record and add `Superseded by ADR-NNNN` to the old one. That
forward reference is the only permitted edit to an accepted record.
