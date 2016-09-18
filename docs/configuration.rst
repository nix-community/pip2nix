Configuration file
==================


Location
--------

pip2nix will search for a configuration file from current working directory up,
until it finds either ``pip2nix.ini`` or ``setup.cfg`` that contains
pip2nix-specific sections.


[pip2nix]
---------

requirements
    comma-separated list of packages to process.

output
    default: ``./python-packages.nix``

    Where to write the generated packages set.


[pip2nix:package:…]
-------------------
