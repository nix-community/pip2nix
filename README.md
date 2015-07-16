# pip2nix

Generate nix expressions for Python packages.

[![Build Status](https://drone.io/github.com/ktosiek/pip2nix/status.png)](https://drone.io/github.com/ktosiek/pip2nix/latest)

# Installation

    $ git clone htts://github.com/ktosiek/pip2nix
    $ nix-env -f pip2nix/release.nix -iA pip2nix.python34  # Same Python as target packages

# Usage

To generate python-packages.nix for a set of requirements:

    $ pip2nix -r requirements.txt

`pip2nix` takes the same set of package specifications pip install does.
