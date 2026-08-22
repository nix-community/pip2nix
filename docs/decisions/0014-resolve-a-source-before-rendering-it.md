---
date: 2026-08-20
---

(adr-0014)=
# ADR-0014 Resolve a source before rendering it

Supersedes {ref}`ADR-0009 <adr-0009>`.

## Context and Problem Statement

{ref}`ADR-0009 <adr-0009>` decided that the renderer resolves a source
hash while it renders, because rendering is where it is known which
values are still missing: a hash the previously generated file already
answered is never fetched.

Rendering a `fetchgit` source therefore calls a prefetch in the middle
of building a string, and rendering an archive re-encodes a digest per
package. The renderer reaches the network and the Nix store, which no
import guard can see, and it is why the output file is opened only
after every package has rendered.

Reading a package's build system needs the checkout, so every
repository is already fetched by the adapter before rendering begins.
The renderer's call answers from the cache rather than being the fetch
the decision was reasoned about.

## Considered Options

1. **Resolve while rendering** — the renderer calls a collaborator for
   a value it cannot render without.
2. **Resolve in the adapter** — the adapter obtains the values and
   hands the renderer a source with nothing left to look up.

## Decision Outcome

Option 2, which {ref}`ADR-0009 <adr-0009>` rejected. Its reasoning does
not hold: the values it wanted to spare were already being fetched a
step earlier, so resolving in the adapter costs nothing and the
renderer becomes a pure function from a package to a string.

Both economies survive because they were never the renderer's. The
prefetch caches on a repository's url and commit id and is handed the
hashes recovered from the previously generated file, and a license
attribute is a different collaborator, which `--licenses` still
switches off.

## Consequences

The renderer reaches nothing outside itself, so a test renders every
kind of source without a collaborator, and a source that arrives
unresolved is refused rather than rendered as an empty value.

The adapter translates what pip reported into what the generated file
fetches with, so a new kind of source has to be added on both sides of
that translation.

{ref}`ADR-0010 <adr-0010>` stands: collaborators are still handed in by
the composition root, fewer of them.
