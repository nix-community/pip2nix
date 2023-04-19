{
  inputs = {
    nixpkgs = {
      type = "github";
      owner = "NixOS";
      repo = "nixpkgs";
      ref = "nixos-20.09";
    };

    flake-utils = {
      type = "github";
      owner = "numtide";
      repo = "flake-utils";
    };
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system: let
      packages = import ./release.nix {
        pkgs = import nixpkgs {
          inherit system;
        };
      };
      defaultPackage = packages.pip2nix.python39;
    in {
      inherit packages defaultPackage;
    });
}

