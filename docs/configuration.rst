Configuration file
==================


Location
--------

pip2nix searches for a ``pip2nix.ini`` carrying pip2nix sections, from the
current working directory up.

Every key below can also be given on the command line, and the command line
wins where both name the same one. An option that is simply not passed does
not count as an answer, so it leaves what the file said alone.


[pip2nix]
---------

requirements
    comma-separated list of packages to process.

    A single value needs no comma. That holds for every list-valued key
    here.

output
    default: ``./python-packages.nix``

    Where to write the generated packages set.

only_direct
    default: ``false``

    Write only the packages that were asked for, instead of everything
    pip resolves.

    Dependencies are unaffected: a package still propagates everything it
    needs, so the generated file refers to attributes it does not define.
    nixpkgs or a lower overlay has to supply them, which is what makes
    layered package sets possible.

excluded_packages
    default: ``pip, setuptools, wheel``

    Packages that are never written to the generated set, however they
    were resolved. Names are matched canonically, so ``zope.interface``
    and ``zope-interface`` are the same entry.

    An excluded package is neither defined nor propagated: no attribute
    is written for it, and no other package lists it under
    ``propagatedBuildInputs``. It can still be named as a build backend
    under ``nativeBuildInputs``, which the generated file does not
    define in any case -- see :doc:`architecture/design`.

    The default is what the build needs of it. The interpreter that
    builds a generated set already provides ``setuptools``, and a second
    definition fails ``pythonCatchConflictsPhase``. ``pip`` is there for
    a stronger reason: it is what a Python package set is bootstrapped
    with, so an attribute defining it shadows the one every other
    package in that set was built by. Shorten the list, or empty it,
    when a set genuinely needs its own version of one of them.

    Exclusion outranks a request: a package named here is dropped even
    when a requirements file asks for it directly. That is the one way
    it differs from ``only_direct``, which stops writing packages while
    leaving the edges that name them.

constraints
    comma-separated list of constraint files, passed to pip as
    ``--constraint``.

    A constraint bounds a package that something else asks for. It does
    not request the package itself, so constraining a package that
    nothing requires has no effect on the generated file.

    A constraint that contradicts a requirement fails the generation.
    Pinning ``markupsafe==3.0.2`` while a requirements file asks for
    ``markupsafe==3.0.3`` is not a narrowing, and pip reports it as
    ``ResolutionImpossible`` rather than choosing one of the two.

index_url
    default: ``https://pypi.python.org/simple``

    The package index to resolve against, passed to pip as
    ``--index-url``.

extra_index_url
    default: empty

    Further indexes to search, passed to pip as ``--extra-index-url``.
    They are searched in addition to ``index_url``, not instead of it.

no_index
    default: ``false``

    Resolve without contacting any index. Both ``index_url`` and
    ``extra_index_url`` are then ignored, so the requirements have to
    name something pip can reach on their own.

licenses
    default: ``false``

    Write ``meta.license`` for each package, read from the metadata the
    index already publishes.

    Only the spellings ``nixpkgs.lib.licenses`` knows are rendered as
    attributes. An SPDX expression resolves to every attribute it names,
    unless it carries ``WITH`` or parentheses, which ``meta.license``
    has no list form for.

    Where nixpkgs knows none of a package's spellings, the most
    authoritative one is kept as a ``{ fullName = ...; }`` and a warning
    names what could not be mapped. That marks a gap in the mapping
    rather than a package without a licence.

    The nixpkgs asked is whichever ``<nixpkgs>`` resolves to in the
    environment the command runs in, and the run names it. Generate
    against the nixpkgs the generated file will be evaluated against,
    since a rendered attribute has to exist there; see
    :ref:`ADR-0015 <adr-0015>`.
