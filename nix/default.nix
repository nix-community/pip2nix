{ nixpkgs ? sources."nixpkgs-20.03"
, config ? {}
, sources ? import ./sources.nix
}:

let

  overlay = _: pkgs: {

    gitignoreSource = (import sources.gitignore {
      inherit (pkgs) lib;
    }).gitignoreSource;

    # pip2nix requires pip version from nixos-20.03
    pip2nix = ((import (sources.pip2nix + "/release.nix") {
      pkgs = import sources."nixpkgs-20.03" {};
    }).pip2nix);

  };

  pkgs = import nixpkgs {
    overlays = [ overlay ];
    inherit config;
  };

in pkgs
