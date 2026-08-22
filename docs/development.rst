Development
===========

Development environment
-----------------------

``nix develop`` gives a shell with the dependencies, ``pytest``, ``just``
and ``pre-commit``. Its own Python carries no pip, so it points
``PIP2NIX_PYTHON_EXECUTABLE`` at one that does -- the interpreter pip2nix
drives, as the built package wraps it.

``just --list`` shows the recipes. CI runs the same ones, so what passes
here is what CI checks.


Running the tests
-----------------

``tests/unit`` needs neither nix nor the network, which makes it the
suite to run while working. ``tests/integration`` needs both, and fails
rather than skips when a tool is missing::

    just test
    just test-integration

Run the integration suite inside ``nix develop``. The shell points
``<nixpkgs>`` at the one the flake locks; outside it, the tests that
evaluate ``<nixpkgs>`` fail at collection rather than waiting on the
flake registry, which fetches without a timeout.

The markers ``nix`` and ``network`` select tests by the infrastructure
they need, so either half runs alone::

    pytest tests/integration/ -m "not network"

Use ``mocker`` or a plain test double; a guard keeps ``monkeypatch`` out
of the suite.


Checking the build
------------------

``just build-all`` builds every supported Python version and the
documentation. Those derivations set ``doCheck = false``, so the suites
above are what test the code.

``just flake-check`` checks the flake on every system it names, where a
plain ``nix flake check`` covers only the system running it. That is
what catches a system nixpkgs has dropped. It exits zero with warnings
present, so the output is worth reading even when it passes.

``just dist-check`` installs the sdist and the wheel and generates with
each, which is what covers an install made without Nix -- see
:doc:`releasing`.


Formatting and linting
----------------------

``ruff`` formats and lints as a pre-commit hook, over the whole tree::

    just lint

The first run fetches its own environment, so it needs the network once.
``pre-commit install`` wires it into ``git commit`` instead.

Do not add ``ruff`` to the development shell. ``.pre-commit-config.yaml``
pins the hook by revision, with the tag beside it in a comment -- see
:ref:`ADR-0012 <adr-0012>` -- and the hook is then the only thing that
formats. The rule selection is named rather than inherited -- see
:ref:`adr-0008`.


Building the documentation
--------------------------

The environment comes from `sphinx-builder`_, a flake input, so the
package list behind Sphinx is not maintained here. Neither is the box
drawing: the builder patches Sphinx's LaTeX style file with the
characters ``pdflatex`` needs to typeset a terminal transcript, which is
why ``conf.py`` declares none of them::

    just docs
    just docs-watch

The PDF is a target of its own, built by neither ``just build-all`` nor
CI because it pulls a texlive distribution nothing else needs. A broken
one surfaces when somebody builds it::

    just docs-pdf

.. _sphinx-builder: https://codeberg.org/johbo/sphinx-builder


Changing the dependencies
-------------------------

After changing the dependencies in ``pyproject.toml``, regenerate
``python-packages.nix`` with the pip2nix you just built. The repository
carries a ``pip2nix.ini`` naming itself as the requirement, so from the
top level directory::

    just regenerate
    just build

``--licenses`` fills the ``meta`` blocks the committed file carries, and
needs a ``<nixpkgs>`` the generator can evaluate. ``pip``, ``setuptools``
and ``wheel`` stay out of the generated set -- :doc:`configuration` says
why. Build again before committing: a regeneration that breaks the build
is the failure mode this step exists to catch.


When something breaks
---------------------

A broken package set cannot regenerate itself, because ``just
regenerate`` needs a pip2nix built from that set. ``just bootstrap``
installs pip2nix into a plain virtualenv instead, and
``_bootstrap_env/bin/pip2nix generate --licenses`` writes a fresh file.

``bad magic number in 'pip2nix.egg_writer'`` comes from a checkout older
than the 0.10.0 release. A stale ``pip2nix.egg-info`` declares an entry
point for a module that has since been removed, and Python imports the
``.pyc`` left beside it although no source remains::

    just clean && just regenerate
