===========
 Changelog
===========


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
