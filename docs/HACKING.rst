Hacking on pip2nix
==================

Development environment
-----------------------

Just running ``nix-shell`` when in the repository should drop you into a shell
with python2.7 and pip2nix wrapper in $PATH. To use a different python, pass
``--argstr pythonPackages python35Packages`` to nix-shell.

Running tests
-------------

To run tests while in the development environment run ``py.test``. It will
search for all tests under current directory.

To test all supported platforms, run ``nix-build ./release.nix`` - this is
actually what CI does.


Changing the dependencies
-------------------------

When changing setup.py you should also run pip2nix to regenerate
python-packages.nix. I you don't have a working copy around, run
``./bootstrap.sh`` from top level directory. The script will install pip2nix
with pip into a virtualenv, and use that to generate python-packages.nix.


Releasing
---------

::

    nix-shell ./release-shell.nix
    bumpversion dev
    rm -rf pip2nix.egg-info/ dist/
    nix-shell --pure --run 'python ./setup.py sdist'
    twine upload dist/*
    bumpversion --no-tag minor
