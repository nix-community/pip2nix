{ pkgs ? (import <nixpkgs> {}) }:

let
  pythonPackages = pkgs.python34Packages.override (a: {
    self = pythonPackages;
  }) // (scopedImport {
    self = pythonPackages;
    super = pkgs.python34Packages;
    inherit pkgs;
    inherit (pkgs) fetchurl;
  } ./release-python-packages.nix);
in pkgs.stdenv.mkDerivation {
  name = "release";
  buildInputs = with pythonPackages; [ twine bumpversion ];
}
