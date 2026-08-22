
======
 Tips
======


Missing build dependencies
==========================

Some Python packages need external libraries or a compiler before their
metadata can be read at all, and that happens while ``pip2nix generate``
resolves rather than when the generated packages are built.

Where an index publishes a package's metadata on its own (:pep:`658`),
pip reads it from there. Where it does not, pip downloads the source
distribution and runs its build backend to obtain the metadata. A
backend that probes for C headers fails at that point:

.. code:: text

    Getting requirements to build wheel: finished with status 'error'
    × Getting requirements to build wheel did not run successfully.
    ╰─> Building lxml version 6.1.1.
        Building without Cython.
        Error: Please make sure the libxml2 and libxslt development
        packages are installed.

pip2nix reaches that path more often than a plain ``pip install`` does,
because it asks pip for the source distribution of every wheel that is
built for a specific platform -- see :ref:`ADR-0003 <adr-0003>`.

The remedy is to make the libraries available to the generation run
itself:

.. code:: shell

   nix shell nixpkgs#libxml2 nixpkgs#libxslt \
       --command pip2nix generate -r requirements.txt

The package may never appear in the generated file. Resolution covers
the whole dependency graph while ``only_direct`` narrows only what is
written, so the generation can fail on headers for a package that
several generated packages propagate and none of them defines.

A package building a Rust or C extension wants its toolchain the same
way, and a compiler counts as part of it: ``nixpkgs#rustc`` and
``nixpkgs#cargo`` on their own leave every Rust build script failing
with ``linker `cc` not found``.

.. code:: shell

   nix shell nixpkgs#rustc nixpkgs#cargo nixpkgs#gcc \
       --command pip2nix generate -r requirements.txt

Expect that to be slow. Building such a package's metadata means
compiling it -- for ``maturin``, minutes of compilation for a few lines
of the generated file.


A pinned build requirement
==========================

A project declaring a build system is generated with
``format = "pyproject"``, and that builder checks
``build-system.requires`` against the environment before it starts. The
generated file names build backends without pinning them, so nixpkgs
decides which version answers a name -- which satisfies a range, but
not an exact pin:

.. code:: text

    ERROR Missing dependencies:
          setuptools==80.9.0

The remedy belongs in the overrides file, where it reaches the one
package that needs it:

.. code:: nix

   httptools = super.httptools.overridePythonAttrs (_: {
     pypaBuildFlags = [ "--skip-dependency-check" ];
   });

That drops the check alone -- the build still takes its dependencies
from ``nativeBuildInputs``. See :ref:`ADR-0004 <adr-0004>`.


Falling back to the previous generator
======================================

pip2nix obtains its dependency graph from pip's installation report --
see :ref:`ADR-0001 <adr-0001>`. The design it replaced drove pip's
internal resolver instead, and what follows from the change is listed
under *Known limits* in :doc:`architecture/design`.

Where that costs a generation that used to work, the fallback is the
revision tagged ``working-generator-2``, which keeps generating
untouched::

    $ nix build 'git+https://github.com/johbo/pip2nix?ref=refs/tags/working-generator-2'

It pins nixpkgs 22.11, Python 3.11 and pip 20.1.1, and it reads the same
``pip2nix.ini`` the current generator does, so a consumer needs no
change to generate with it.

Do not reach for the older ``working-generator`` tag. It resolves a git
revision only where the requirement spells it out fully, as
``@refs/heads/main``, and for anything else it writes a truncated,
unparseable file while exiting zero.
