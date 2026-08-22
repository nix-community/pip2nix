==========
Principles
==========

Rules that hold across pip2nix rather than in one part of it.

Pinning is the point
====================

Every source carries a sha256. An archive takes the one the index
published, and a source the index published none for aborts the run
rather than producing an unpinned ``fetchurl``; a repository takes the
one its fetch reports, which the previously generated file may have
answered. Hashes are
written in the base32 alphabet Nix uses, so that regenerating a file
shows what changed rather than how it was encoded.

Names are canonical
===================

Packages are named by their canonical name as defined in PEP 503, both
as attributes and in the references between them. pip2nix owns no
naming rule of its own, and a package cannot appear under two names
because two dependents spelled it differently. See :ref:`ADR-0002 <adr-0002>`.

pip stays at arm's length
=========================

pip is a subprocess, not a library. Its argument vector is a list, so
requirement strings out of a configuration file never reach a shell,
and its report is validated before it is trusted. Nothing on the path
imports ``pip._internal``, and a test enforces that.

Collaborators are handed in
===========================

What a block needs from outside itself is declared where it is needed
and satisfied where the technology lives. The adapter states that it
needs a source fetched and the renderer that it needs a license
attribute; the composition root is the only place that decides a
prefetch and a query to nixpkgs are what answer them. Nothing reaches
for a collaborator it was not given, which is what lets a test pass a
simpler one in. See :ref:`ADR-0010 <adr-0010>`.

Failures are loud
=================

A generator that writes a plausible file is worse than one that stops.
An unresolvable revision, a missing hash, and a requirement kind the
generator cannot express all abort the run. The previous output
survives and the exit status says what happened.

A generated layer and a customization layer
===========================================

Perfect Nix expressions cannot be generated from Python metadata,
because the metadata does not carry what Nix needs to know: which C
libraries a package links against, which build tools it expects, which
patches it needs. Nothing can supply what was never declared, so a
generator that aimed for completeness would have to guess.

pip2nix assumes two layers instead. The generated layer holds what the
metadata does support -- names, versions, pinned sources and
dependency edges -- and is overwritten wholesale on every
regeneration. At least one customization layer sits on top of it,
hand-maintained, adding native dependencies and build fixes; this is
what ``pip2nix scaffold`` creates the overrides file for.

Roughly, generation covers the routine four fifths and the
customization layer covers the rest. The split is what keeps the
generator small, and it is what makes a regeneration safe: overwriting
the generated layer cannot destroy the knowledge that was added by
hand.
