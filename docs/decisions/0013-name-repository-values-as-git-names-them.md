---
date: 2026-08-20
---

(adr-0013)=
# ADR-0013 Name repository values as git names them

## Context and Problem Statement

pip2nix spells three different values `rev`. A `Repository` is built
from pip's `commit_id` and always holds a 40-hexadecimal object name.
`prefetch_git` takes a value that may be a branch name, a tag or a
commit ID. Nix's `fetchgit` declares an attribute of that name.

Git has a word for each of the three. Using one spelling for all of
them means a name does not say how wide its value is, and a docstring
has to.

## Considered Options

1. **Keep `rev` throughout** — the spelling the generated file emits,
   used for every repository value whatever its width.
2. **Adopt git's vocabulary** — name each value with git's own word
   for what it is.

## Decision Outcome

A repository value takes git's word for what it is: a 40-hexadecimal
object name is a **commit ID**, a value that may be a branch, a tag or
a commit is a **revision**, and a named pointer under `refs/` is a
**reference**.

A name that says commit ID is a claim the type can be held to, where
`rev` leaves it to a docstring. Git settled these words, and both
pip's report and the git tooling already use them, so pip2nix inherits
a vocabulary rather than inventing one. Keeping `rev` throughout was
rejected because one spelling for three widths reads as consistency
while hiding which value is which.

## Consequences

`rev` survives where it is Nix's name rather than pip2nix's — in the
generated file, and on the type modelling `fetchgit`'s arguments. One
concept therefore has two spellings, meeting at the adapter that
translates between them.

The three terms are defined in the glossary.
