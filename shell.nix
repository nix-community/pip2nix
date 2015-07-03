let
  pkgs = import <nixpkgs> {};
  pip2nix = import ./.;
in pkgs.lib.overrideDerivation pip2nix (a: {
  src = null;
  nativeBuildInputs = a.nativeBuildInputs ++ [pkgs.pythonPackages.ipdb];
})
