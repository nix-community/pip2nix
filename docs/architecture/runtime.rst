================
A generation run
================

1. ``cli.py`` loads the configuration, merges the command line over it,
   and builds the ``Resolver`` that carries it to pip.
2. ``resolver.py`` derives pip's argument vector from it and runs
   ``pip install --dry-run --ignore-installed --report`` into a
   temporary directory it owns. That pip has to be 22.2 or newer, the
   release that learned to write a report, which is checked before the
   run starts.
3. The report's ``version`` field is checked before anything in it is
   read.
4. The entries named by ``excluded_packages`` are dropped, before any
   edge is attributed, so that nothing left in the run can refer to
   them.
5. ``dependencies.py`` attributes the edges: markers are evaluated
   against the environment the report resolved for, extras are
   propagated to the packages they reach, and the result is
   intersected with the resolved set.
6. Each entry becomes a package: an archive carries the hash the index
   published, a repository the commit id pip resolved. Under
   ``only_direct`` only the entries pip marked as requested are kept --
   after attribution, so that what is kept still propagates what it
   needs.
7. A package left holding a wheel that is built for a platform gets its
   source replaced by the project's source distribution, resolved by a
   run of its own that refuses a wheel to that package alone. A run
   with none of them starts no further resolution.
   See :ref:`ADR-0003 <adr-0003>` for which packages this reaches and
   :ref:`ADR-0005 <adr-0005>` for why each gets its own pass.
8. Every package that is built from source is read for the build
   backend it declares, which means fetching the archive or the
   checkout it will be built from. Both fetches are handed the hash
   that is already known, so nix answers from the store rather than
   downloading or cloning again. That read also decides how the package
   is built: a source declaring a ``[build-system]`` table is emitted as
   ``pyproject``, one without it as ``setuptools``, and a wheel as
   ``wheel``. The renderer is handed the answer rather than deriving it
   from the file name.
9. Every source is then resolved into what the generated file fetches
   with: a repository into the commit id and hash its fetch reported,
   an archive into the digest the report carried, written in the
   alphabet Nix reads. The repository was fetched by the step above or
   answered by the previously generated file, so this adds no clone.
   See :ref:`ADR-0014 <adr-0014>`.
10. ``output.py`` renders every package and writes the result. No
    source is looked up while it runs: every value a package fetches
    with was resolved before rendering started. A repository is
    recorded under its url and its commit id, both of which name
    immutable content, so a hash recovered for the pair needs no
    checking.

A license attribute is the one lookup rendering still makes, and
``--licenses`` off removes even that one: the composition root then
hands down a collaborator that renders no license, rather than a flag
for the renderer to read. That lookup is why rendering finishes before
the output file is opened — a failure then leaves the previous file
intact instead of truncating it.
