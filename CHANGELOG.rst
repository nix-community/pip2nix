===========
 Changelog
===========


0.5.0
=====

- Fixes for git URL support, parsing the output of `nix-prefetch-git` as JSON.

- Use `nix-prefetch-url` to fetch dependencies and get their `sha256` hash.

- Allow version 9 of pip itself for better compatibility with recent nixpkgs
  versions.

- Update `python-packages.nix` and `release-python-packages.nix`. This should
  also avoid the warnings due to using `md5` as a hash type.
