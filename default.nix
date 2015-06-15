let
  pkgs = import <nixpkgs> {};
  pythonPackages = pkgs.python27Packages // scopedImport {
    self = pythonPackages;
    inherit (pkgs) fetchurl;
  } ./python-packages.nix;
in pythonPackages.pip2nix
