===========
 Changelog
===========

All notable changes to this project will be documented in this file.

The format is based on `Keep a Changelog
<https://keepachangelog.com/en/2.0.0/>`_, and this project adheres to
`PEP 440 <https://peps.python.org/pep-0440/>`_.

.. towncrier release notes start

0.13.1 - 2026-08-21
===================

Fixed
-----

- Build from the files git tracks, so a stale ``build/`` in the working
  tree cannot reach the build. Nix copies the whole working directory
  into the store for a dirty tree without consulting ``.gitignore``, and
  setuptools then reuses the ``build/lib`` it finds there rather than the
  real sources -- which produced a generator several changes out of date
  while reporting success.


0.13.0 - 2026-08-21
===================

Changed
-------

- Exclude ``pip`` from the generated file by default, beside
  ``setuptools`` and ``wheel``. An attribute named ``pip`` shadows the one
  nixpkgs bootstraps its Python package set with, so a requirement set
  that resolves pip would otherwise generate a file that breaks the
  overlay composing it.
- Name the nixpkgs a license query is answered by, and give up on one
  that does not resolve. ``--licenses`` evaluates ``<nixpkgs>``, which
  resolves from ``NIX_PATH``, so which nixpkgs answered depended on the
  environment the command ran in without the run saying which it was. The
  store path is now reported before the query, and a ``<nixpkgs>`` that
  does not resolve fails after 30 seconds instead of blocking on a fetch
  from the flake registry; see ADR-0015.
- Pin the ``ruff`` pre-commit hook by revision rather than by tag, with
  the tag it came from in a comment beside it. A tag can be repointed at
  the remote, so the configuration now names the revision that lints the
  tree; see ADR-0012.
- Render the box drawing in the PDF documentation as box drawing. The
  transcript in the tips chapter printed ``+->`` where pip writes
  ``╰─>``, because the substitutions declared for ``pdflatex`` also
  overrode the glyph Sphinx draws for ``─`` itself.
- Stop reaching for ``git``. A repository source is fetched at the commit
  pip already resolved it to, so no branch or tag is looked up any more
  and ``git`` no longer has to be on ``PATH`` -- ``nix-prefetch-git``
  brings its own.


Fixed
-----

- Declare ``pip`` as a dependency, so an install outside Nix brings the
  resolver it runs. Resolution drives ``python -m pip`` in the
  environment pip2nix is installed into, and an environment created by
  ``uv`` carries no pip, which made every run of such an install fail.
- Report a source url pip2nix cannot render as an error rather than a traceback


0.12.0 - 2026-08-19
===================

Added
-----

- Build and test against Python 3.14, alongside 3.11 to 3.13.
  ``nix build`` still defaults to 3.13, and ``.#pip2nix_python314``
  builds the new target.
- Check the flake on every system it names, as ``just flake-check`` and
  as a job of its own in CI. ``nix flake check`` alone covers the system
  running it, so an output that fails to evaluate on one of the others
  stayed invisible until somebody built it. The run exits zero with
  warnings present, so its output is worth reading even when it passes.
- Document ``index_url``, ``extra_index_url``, ``no_index`` and
  ``licenses``, bringing the configuration reference to the whole
  surface. Its claim that a ``setup.cfg`` is searched for pip2nix
  sections is dropped -- only ``pip2nix.ini`` ever was.
- Install a versioned command naming the interpreter a build resolves
  against, ``pip2nix3.13`` beside ``pip2nix`` for the default target.
  Nix builds it, because Nix is what knows the interpreter.


Changed
-------

- **Breaking:** Require Python 3.11. The 3.10 release target built, but
  the built package could not be imported: ``build_system.py`` reads
  ``tomllib``, which is stdlib from 3.11 on. ``setup.py`` declares
  ``python_requires`` now, and the classifiers name the versions that
  actually work rather than Python 2.7 through 3.6.
- Announce a prefetch on stderr rather than on stdout. The two
  remaining ``print`` calls became log records at INFO level, so a
  run's progress goes to the stream its warnings already use and
  carries the same ``INFO:`` prefix. The announcements stay visible at
  default verbosity, and a prefetch answered from a recorded hash stays
  silent as before.
- Format and lint with ``ruff`` alone, on a rule selection the
  configuration names rather than inherits. ``docformatter`` is gone and
  ``D213`` enforces the docstring layout it enforced, so wrapping prose
  is the author's again; see ADR-0008.
- Migrate pip2nix's own packaging to ``pyproject.toml``. It decides how
  to build a package from that package's ``[build-system]`` table, and
  shipped a ``setup.py`` itself -- so it now declares what it expects
  everything it generates to declare, and writes ``format =
  "pyproject"`` for its own entry.
- Name this fork beside upstream in the header of every generated file.
  It credited ``nix-community/pip2nix`` alone, which no longer wrote the
  file. Both urls stand until the work merges back, when one of them
  goes again.
- Render the documentation's copyright year from the last commit rather
  than from a pin kept in step by hand. ``conf.py`` writes ``2015-%Y``
  and the flake passes ``self.lastModified``, so the year advances on
  its own and an old revision keeps rendering the year it was written
  in. Both documentation builds refuse an epoch from before the project
  existed, which is what ``stdenv``'s 1980 default would otherwise put
  in the footer.
- Replace the release tooling with a ``nix develop .#release`` shell
  carrying ``bump-my-version``, the build frontend and ``twine``, and
  add ``just dist`` to build the source distribution and the wheel.
  ``release-shell.nix`` and the package set it read, generated in 2018
  against ``python36Packages``, are gone.
- Stop cloning a repository the Nix store already holds. The hash a
  ``fetchgit`` source was generated with is recovered from the previous
  file, keyed on the url and the revision together, and handed to
  ``nix-prefetch-git``, which then answers from the store. A regeneration
  of a consumer built on git sources re-clones none of them, and the
  generated file does not move. Nothing roots those store paths, so a
  garbage collection puts the clones back.
- Update the nixpkgs pin from 2025-11-18 to 2026-08-17, and name the
  systems the flake supports rather than taking them from
  ``eachDefaultSystem``. That list comes from ``nix-systems/default``,
  unchanged since 2023, and still carries ``x86_64-darwin`` -- a system
  nixpkgs dropped in 26.11, which made every output under it fail to
  evaluate. ``python-packages.nix`` regenerates byte for byte across
  the bump, pip 25.0.1 to 26.1.2 included.


Removed
-------

- **Breaking:** Remove per-package configuration. The
  ``[pip2nix:package:…]`` section, with ``additional_requirements``,
  ``excluded_requirements`` and ``args``, was parsed and never applied
  to anything pip2nix generated. A file that declares one now fails
  validation instead of reporting success. Customize a generated
  package in the overrides layer beside the generated file. See
  ADR-0006.
- Drop the versioned console scripts ``pip2nix3`` and ``pip2nix3.1``.
  They were computed from ``sys.version`` slices yielding ``"3"`` and
  ``"3.1"`` on every supported interpreter, so all three builds
  installed the same two names and neither said which interpreter it
  resolves against.
- Stop emitting ``checkInputs``. It was written as an empty list on
  every package and filled on none, and an omitted argument takes
  ``buildPythonPackage``'s own default, so no build changes. Test
  dependencies stay the customization layer's, where
  ``nativeCheckInputs`` is the attribute for them; see ADR-0011.


Fixed
-----

- Accept a single value wherever a list is expected. ``constraints``,
  ``excluded_packages`` and ``extra_index_url`` refused
  ``constraints = constraints.txt`` and wanted a trailing comma,
  reporting its absence as a type error that said nothing about commas.
  ``requirements`` always accepted it.
- Fix three options a ``pip2nix.ini`` could not set. ``no_index``,
  ``licenses`` and ``extra_index_url`` were overwritten by the command
  line's own defaults, so a file that set them was ignored without
  saying so. ``licenses`` was additionally read while declared in no
  configuration spec, and can be set in a file at all for the first
  time.
- Put the tools pip2nix runs on the PATH of the entry points
  ``default.nix`` wraps. A built pip2nix found ``nix-prefetch-url`` and
  ``nix-instantiate`` only where ``nix`` happened to be on the ambient
  PATH, and ``nix-prefetch-git`` -- which every ``fetchgit`` source
  needs -- nowhere at all.


0.11.0
======

- **Breaking:** Render `format` from the build backend a project
  declares rather than from the file extension. A source carrying a
  `[build-system]` table renders `format = "pyproject"`, one without --
  a bare `setup.py` project among them -- stays `setuptools`, and a
  wheel stays `wheel`. A hatchling project used to install with the
  setuptools builder while the backend it declared sat unused in
  `nativeBuildInputs`.

  Regenerating moves the affected packages to the other builder, and
  the pyproject builder checks `build-system.requires` where the
  setuptools one never read it. A package that pins a build requirement
  exactly -- `httptools` requires `setuptools==80.9.0` -- then fails to
  build and wants `pypaBuildFlags = [ "--skip-dependency-check" ]` in
  the overrides layer. See ADR-0004.

- Stop building a package's build backend while resolving another
  package from source. A source distribution is asked for in a run of
  its own now, which refuses a wheel to that one package, so a backend
  that is emitted beside the packages it builds -- `maturin` is the
  case -- is installed rather than compiled. See ADR-0005.

- Drop the `setuptools` dependency. The data files pip2nix ships are
  read through `importlib.resources` now, so installing it no longer
  needs a setuptools old enough to carry `pkg_resources`.

- Fix `pip2nix scaffold`: the `default.nix` it writes evaluates now. It
  called `composeExtensions` without bringing it into scope, and
  overrode the package with `.override`, which `buildPythonPackage`
  does not carry -- `.overridePythonAttrs` is the one that does.

- `pip2nix scaffold --package` canonicalizes the name it is given, so
  the scaffold refers to the package under the name the generated file
  defines it under, per ADR-0002. A name that starts with a digit no
  longer produces a syntax error either.

- **Breaking:** Drop the `--no-binary`, `--build` and `--download`
  flags. All three were accepted and then ignored: the report path
  unpacks nothing and downloads to no directory of its own, and whether
  a package is taken from its source distribution is decided per
  package now, by the rule in ADR-0003.

- **Breaking:** Reject an editable requirement given as `-e` on the
  command line. It was folded into the plain specifiers, so `pip2nix
  generate -e .` resolved `.` non-editable and generated a file, where
  the same requirement in `pip2nix.ini` or in a requirements file
  aborts the run.


0.10.0
======

- Generate from pip's installation report rather than from pip's
  internal resolver API. pip runs as a subprocess, so pip2nix is no
  longer bound to pip 20.1.1: any pip from 22.2 on will do, which is
  checked before a run starts. It is a runtime dependency now and is not
  declared in `install_requires` any more. See ADR-0001.

- **Breaking:** Drop support for mercurial requirements. Only git
  repositories are rendered, and an `hg+` requirement aborts the run
  instead of resolving. Generated files keep taking `fetchhg` as an
  argument, so the ones consumers already have go on evaluating.

- **Breaking:** Drop `checkInputs` and the `--check-inputs` flag. The
  test dependencies were read out of a file pip2nix wrote into each
  package while it was being built, which the report path never does,
  and the setuptools field they came from is deprecated. With
  `doCheck = false` on every generated package the field only had an
  effect for a consumer overriding that as well.

- Resolve the revision of a git requirement the way pip does, so that a
  bare branch name works again and a branch takes precedence over a tag
  of the same name. Previously the requested revision either had to be
  written fully qualified, as `@refs/heads/main`, or the source was
  fetched from the default branch regardless of what was asked for.

- Abort the generation when a revision cannot be resolved, instead of
  dropping the package from the output.

- Keep the previously generated file intact when the generation fails,
  and exit with a non-zero status. Both used to be silent: the output
  was truncated to an unparseable fragment and the command still
  reported success.

- Drop the `toml` dependency. `pyproject.toml` is read with the standard
  library's `tomllib`.

- Adopt decision records. Significant decisions are now recorded as ADRs
  under `docs/decisions/`, rendered in the documentation as the decision
  log. The conventions are described in `docs/decisions/README.md`.

- Record the decision to generate from pip's installation report instead
  of driving pip's internal API. See ADR-0001.

- **Breaking:** Name generated packages by their canonical name as
  defined in PEP 503, so that `Genshi` is now written `genshi` and
  `PyYAML` is written `pyyaml`. A package used to be named after
  whichever requirement first asked for it, which meant the same package
  could appear under two names in different files. Overrides written for
  the old spellings have to be renamed, and aliases that only existed to
  reach a nixpkgs attribute can usually be dropped. See ADR-0002.

- Write a package that is both constrained and required when
  `only_direct` is set. It used to be dropped while other packages kept
  propagating it, so the generated file referred to an attribute that
  nothing defined.

- Make the packages that are kept out of the generated set
  configurable, as `excluded_packages`. It defaults to `setuptools` and
  `wheel`, which is what pip2nix has always excluded, and a set that
  needs its own version of either can now say so.

- Fail the generation when a constraint contradicts a requirement,
  which is what pip now reports as `ResolutionImpossible`. The two used
  to be merged silently, with the constraint winning and the package
  disappearing from the output.

- Read the licenses out of pip's installation report, which carries
  `License`, `License-Expression` and the license classifiers alike, so
  `--licenses` no longer unpacks a built distribution to find them. An
  SPDX identifier resolves to the matching `lib.licenses` attribute on
  its own.

- Render only the license spellings nixpkgs knows, and fall back to a
  single `{ fullName = ...; }` when it knows none of them. A package
  declaring both a version-less `License` and a precise classifier used
  to emit the vague reading next to the exact one.

- Fix the query behind the license lookup, which raised for every
  license outside the built-in mapping once `lib.licenses` grew the SPDX
  operators, and stop mapping an unversioned `GPL` onto
  `lib.licenses.gpl1`, which nixpkgs has removed.

- Generate the source distribution of a package whose wheel is built for
  a platform, instead of that wheel. Such a wheel links against
  libraries at paths that do not exist in the store, so the derivation
  built and then failed on import. A `-any` wheel carries the same
  modules its source distribution does and keeps being used as it is.
  See ADR-0003.

- Render `nativeBuildInputs` from the `build-system.requires` a source
  declares, read out of the source distribution, the local directory or
  the git checkout being generated from. pip's installation report
  carries core metadata, which has no build-system field. The names are
  canonical per ADR-0002, where they used to be spelled as declared, and
  a backend declared twice is named once.

- Build the release targets for Python 3.10 to 3.13 only. The `python27`
  target failed to evaluate, since nixpkgs marks Python 2.7 insecure,
  and the targets between 3.3 and 3.9 named package sets nixpkgs no
  longer provides.

- Fix the `docs` job in `release.nix`, which built the documentation
  with a Python nixpkgs no longer has and without the parser the
  decision records need.

- Drop the `niv` sources, `bootstrap.sh` and `shell.nix`. The flake is
  the only build path now: `nix develop` replaces `shell.nix`, and the
  commands that used to live only in the documentation are recipes in a
  new `justfile`, which the CI workflow runs as well. `just bootstrap`
  keeps what `bootstrap.sh` was for, a pip2nix built without the
  generated package set.

- Fix job `docs` in `release.nix` to include the full sources.

- Extend tips in the documentation with trouble related to `nix-prefetch-hg`.

- Number this release 0.10.0. It follows 0.7.0: the development
  versions in between announced a 0.8.0 and a 0.9.0 that were never
  released, and the numbering stays clear of the line the project is
  forked from.


0.7.0
=====

- Update template for the file `default.nix` to also ignore the `.hg` folder.
  This is useful for Mercurial based projects.

  Thanks to Marcin Kuzminzki.

- Fix to quote package and dependency names and improve the readability of the
  generated output.

  Thanks to Asko Soukka.

- Adjust `release.nix` for better Hydra integration.

  Thanks to Martin Bornhold.

- Mark tests as xfail to avoid trouble when building on NixOS itself.
  Details can be found here https://github.com/johbo/pip2nix/issues/35.

- Use `python36Packages` by default inside of `default.nix`. I noticed that I
  was specifying it nearly always when working on `pip2nix`. Via `release.nix`
  we still have all Python versions easily available.

- Fix the attribute name of ZPL licenses, so that it matches the attribute names
  from Nixpkgs_.

- Add an example about `setuptools` into the generated layer with manual
  overrides. This is a useful entry when running into issues around an infinite
  recursion.

- Update docs with a hint how to run inside of `nix-shell`.

- Update docs with a pointer to examples in `pip2nix-generated`.

- Add section "Tips" to the documentation.


0.6.0
=====

- Change the file `python-packages.nix` into a function.

  To adjust import it like the following:

  .. code:: nix

      pythonPackagesGenerated = import ./python-packages.nix {
        inherit pkgs;
        inherit (pkgs) fetchurl fetchgit;
      };

- Add new attribute `pip2nix.python36` into the file `release.nix`.

- Adjust the template for the file `default.nix` to be compatible with
  the new python packages which are based on the fix point combinator.
  See https://github.com/NixOS/nixpkgs/pull/20893 for more details.


0.5.0
=====

- Fixes for git URL support, parsing the output of `nix-prefetch-git` as JSON.

- Use `nix-prefetch-url` to fetch dependencies and get their `sha256` hash.

- Allow version 9 of pip itself for better compatibility with recent nixpkgs
  versions.

- Update `python-packages.nix` and `release-python-packages.nix`. This should
  also avoid the warnings due to using `md5` as a hash type.





.. Links

.. _Nixpkgs: https://nixos.org/nixpkgs
