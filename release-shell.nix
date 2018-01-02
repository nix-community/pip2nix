{ pkgs ? (import <nixpkgs> {})
, pythonPackages ? "python36Packages"
}:

with pkgs.lib;
let
  basePythonPackages = with builtins; if isAttrs pythonPackages
    then pythonPackages
    else getAttr pythonPackages pkgs;

  # Works with the new python-packages, still can fallback to the old
  # variant.
  basePythonPackagesUnfix = basePythonPackages.__unfix__ or (
    self: basePythonPackages.override (a: { inherit self; }));

  pythonPackagesLocalOverrides = self: super: {
    setuptools = basePythonPackages.setuptools;
  };

  pythonPackagesGenerated = import ./release-python-packages.nix {
    inherit pkgs;
    inherit (pkgs) fetchurl fetchgit fetchhg;
  };

  myPythonPackages =
    (fix
    (extends pythonPackagesLocalOverrides
    (extends pythonPackagesGenerated
             basePythonPackagesUnfix)));

in pkgs.stdenv.mkDerivation {
  name = "release";
  buildInputs = with myPythonPackages; [ twine bumpversion ];
}
