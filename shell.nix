{ pkgs ? (import <nixpkgs> {}), pythonPackages ? "python27Packages" }@args:
let
  pip2nix = import ./. args;
in pkgs.lib.overrideDerivation pip2nix (a: {
  src = null;
  #nativeBuildInputs = a.nativeBuildInputs ++ [pkgs.pythonPackages.ipdb];
})
