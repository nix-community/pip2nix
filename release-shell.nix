{ pkgs ? (import <nixpkgs> {}) }:

let
  pythonPackages = pkgs.python35Packages.override (a: {
    self = pythonPackages;
  }) // (scopedImport {
    self = pythonPackages;
    super = pkgs.python35Packages;
    inherit pkgs;
    inherit (pkgs) fetchurl;
  } ./release-python-packages.nix) // {
    inherit (pkgs.python35Packages) setuptools;
  };
in pkgs.stdenv.mkDerivation {
  name = "release";
  buildInputs = with pythonPackages; [ twine bumpversion ];
}
